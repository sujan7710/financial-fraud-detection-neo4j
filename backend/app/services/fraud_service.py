import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from app.config import settings
from app.database import db
from app.models.pattern import (
    DetectionReportSummary,
    FlaggedPattern,
    FraudDetectionReport,
    PatternSeverity,
    SuspiciousPatternType,
)

logger = logging.getLogger("fraud_detection.services.fraud")

class FraudDetectionService:
    @staticmethod
    def detect_circular_transactions(
        min_depth: int = 3,
        max_depth: int = 5
    ) -> List[FlaggedPattern]:
        """
        Detect closed cycles of financial transfers using Cypher variable-length path traversal.
        A -> B -> C -> ... -> A
        Layering technique used to disguise illicit money trails.
        """
        query = f"""
        MATCH path = (origin:Account)-[r:SENT*{min_depth}..{max_depth}]->(origin)
        WITH path,
             [rel IN relationships(path) | rel.transaction_id] AS tx_ids,
             [rel IN relationships(path) | rel.amount] AS amounts,
             [node IN nodes(path) | node.account_id] AS acc_ids
        RETURN acc_ids, tx_ids, amounts, length(path) AS cycle_length
        """
        patterns: List[FlaggedPattern] = []
        seen_cycle_fingerprints: Set[frozenset] = set()

        try:
            records = db.execute_read(query)
            for rec in records:
                acc_ids = rec.get("acc_ids", [])
                tx_ids = rec.get("tx_ids", [])
                amounts = rec.get("amounts", [])
                cycle_len = rec.get("cycle_length", len(tx_ids))

                # Normalize cycle nodes (first element matches last element)
                unique_nodes = frozenset(acc_ids[:-1] if len(acc_ids) > 1 and acc_ids[0] == acc_ids[-1] else acc_ids)
                if unique_nodes in seen_cycle_fingerprints:
                    continue
                seen_cycle_fingerprints.add(unique_nodes)

                total_cycle_amount = round(sum(amounts), 2)
                cycle_path_str = " ➔ ".join(acc_ids)
                pattern_id = f"PAT-CIRC-{abs(hash(unique_nodes)) % 1000000:06d}"

                pattern = FlaggedPattern(
                    pattern_id=pattern_id,
                    pattern_type=SuspiciousPatternType.CIRCULAR_TRANSACTION,
                    severity=PatternSeverity.CRITICAL,
                    rule_name="Circular Fund Routing (Layering Cycle)",
                    summary=f"Detected {cycle_len}-hop closed circular transaction ring involving {len(unique_nodes)} accounts.",
                    explainability=(
                        f"Financial transfers followed a closed loop sequence ({cycle_path_str}) "
                        f"where funds returned to the originating entity or an affiliated node. "
                        f"In forensic graph analysis, cyclic routing with matching or decaying values "
                        f"is a strong indicator of money laundering layering designed to generate artificial trade volume or obscure ownership."
                    ),
                    recommended_action=(
                        "1. Place temporary debit hold on all participating accounts. "
                        "2. Perform comprehensive Ultimate Beneficial Owner (UBO) cross-referencing. "
                        "3. File FinCEN / FIU Suspicious Activity Report (SAR) citing circular layering topology."
                    ),
                    involved_accounts=list(acc_ids),
                    involved_transactions=tx_ids,
                    total_amount=total_cycle_amount,
                    cypher_query_used=query.strip(),
                    metadata={
                        "cycle_length": cycle_len,
                        "unique_account_count": len(unique_nodes),
                        "amounts": amounts,
                        "path": acc_ids
                    }
                )
                patterns.append(pattern)
        except Exception as e:
            logger.error(f"Error executing circular pattern detection: {str(e)}")

        return patterns

    @staticmethod
    def detect_large_transactions(
        threshold: Optional[float] = None
    ) -> List[FlaggedPattern]:
        """
        Detect outlier transactions exceeding the configured threshold.
        """
        thresh = threshold if threshold is not None else settings.LARGE_TRANSACTION_THRESHOLD
        query = """
        MATCH (source:Account)-[r:SENT]->(target:Account)
        WHERE r.amount >= $threshold
        RETURN r.transaction_id AS tx_id,
               source.account_id AS from_account_id,
               source.customer_name AS from_name,
               source.account_type AS from_type,
               target.account_id AS to_account_id,
               target.customer_name AS to_name,
               target.account_type AS to_type,
               r.amount AS amount,
               r.currency AS currency,
               r.channel AS channel,
               r.timestamp AS timestamp
        ORDER BY r.amount DESC
        """
        patterns: List[FlaggedPattern] = []
        try:
            records = db.execute_read(query, {"threshold": float(thresh)})
            for rec in records:
                tx_id = rec.get("tx_id")
                amount = float(rec.get("amount", 0.0))
                from_id = rec.get("from_account_id")
                to_id = rec.get("to_account_id")
                from_name = rec.get("from_name")
                to_name = rec.get("to_name")
                channel = rec.get("channel", "WIRE")
                timestamp = rec.get("timestamp")

                severity = PatternSeverity.CRITICAL if amount >= thresh * 5.0 else PatternSeverity.HIGH
                pattern_id = f"PAT-LRG-{tx_id}"

                pattern = FlaggedPattern(
                    pattern_id=pattern_id,
                    pattern_type=SuspiciousPatternType.LARGE_TRANSACTION_OUTLIER,
                    severity=severity,
                    rule_name="High-Value Transaction Outlier",
                    summary=f"Outlier transfer of ${amount:,.2f} from {from_id} ({from_name}) to {to_id} ({to_name}).",
                    explainability=(
                        f"Transaction {tx_id} of ${amount:,.2f} via {channel} significantly exceeds "
                        f"the regulatory threshold (${thresh:,.2f}). "
                        f"Transfer from '{from_name}' to '{to_name}' represents a concentrated capital movement "
                        f"requiring independent verification of commercial purpose and source of wealth."
                    ),
                    recommended_action=(
                        "1. Request commercial supporting invoices and source-of-wealth documentation. "
                        "2. Verify counterparty identity against international sanctions screening lists."
                    ),
                    involved_accounts=[from_id, to_id],
                    involved_transactions=[tx_id],
                    total_amount=amount,
                    cypher_query_used=query.strip(),
                    metadata={
                        "from_customer": from_name,
                        "to_customer": to_name,
                        "channel": channel,
                        "timestamp": timestamp,
                        "threshold_applied": thresh
                    }
                )
                patterns.append(pattern)
        except Exception as e:
            logger.error(f"Error executing large transaction detection: {str(e)}")

        return patterns

    @staticmethod
    def detect_smurfing_structuring(
        sub_threshold: Optional[float] = None,
        min_accounts: Optional[int] = None
    ) -> List[FlaggedPattern]:
        """
        Detect structuring / smurfing:
        1. Fan-In: Multiple sender accounts transferring amounts just below CTR limit ($10,000)
           into a central hub account.
        2. Fan-Out: A single account dispersing funds to multiple recipients in sub-threshold tranches.
        """
        sub_max = sub_threshold if sub_threshold is not None else settings.SMURFING_SUB_THRESHOLD
        sub_min = sub_max * 0.70  # e.g., $7,000 - $9,999.99 for a $10,000 threshold
        min_acc = min_accounts if min_accounts is not None else settings.SMURFING_MIN_ACCOUNTS

        patterns: List[FlaggedPattern] = []

        # 1. Fan-In Smurfing Query
        fan_in_query = """
        MATCH (sender:Account)-[r:SENT]->(hub:Account)
        WHERE r.amount >= $sub_min AND r.amount < $sub_max
        WITH hub, count(DISTINCT sender) AS sender_count,
             collect(DISTINCT sender.account_id) AS sender_ids,
             collect(r.transaction_id) AS tx_ids,
             round(sum(r.amount) * 100.0) / 100.0 AS total_amount
        WHERE sender_count >= $min_acc
        RETURN hub.account_id AS hub_id,
               hub.customer_name AS hub_name,
               sender_count,
               sender_ids,
               tx_ids,
               total_amount
        ORDER BY total_amount DESC
        """

        try:
            records = db.execute_read(fan_in_query, {
                "sub_min": float(sub_min),
                "sub_max": float(sub_max),
                "min_acc": int(min_acc)
            })
            for rec in records:
                hub_id = rec.get("hub_id")
                hub_name = rec.get("hub_name")
                sender_count = rec.get("sender_count", 0)
                sender_ids = rec.get("sender_ids", [])
                tx_ids = rec.get("tx_ids", [])
                total_amount = float(rec.get("total_amount", 0.0))
                pattern_id = f"PAT-SMURF-IN-{hub_id}"

                pattern = FlaggedPattern(
                    pattern_id=pattern_id,
                    pattern_type=SuspiciousPatternType.SMURFING_FAN_IN,
                    severity=PatternSeverity.HIGH,
                    rule_name="Structuring / Smurfing (Fan-In Aggregation)",
                    summary=f"Hub account {hub_id} ({hub_name}) received {sender_count} structured sub-threshold transfers totaling ${total_amount:,.2f}.",
                    explainability=(
                        f"Account {hub_id} collected funds from {sender_count} distinct senders ({', '.join(sender_ids[:4])}{'...' if len(sender_ids) > 4 else ''}) "
                        f"where individual transfer sizes (${sub_min:,.2f} - ${sub_max:,.2f}) were systematically maintained "
                        f"just below mandatory Currency Transaction Report (CTR) filing thresholds. "
                        f"This fan-in topology strongly resembles money mule aggregation networks."
                    ),
                    recommended_action=(
                        "1. Interrogate hub account transaction frequency and beneficial owner declarations. "
                        "2. Perform behavioral linkage analysis on all originating mule accounts."
                    ),
                    involved_accounts=[hub_id] + sender_ids,
                    involved_transactions=tx_ids,
                    total_amount=total_amount,
                    cypher_query_used=fan_in_query.strip(),
                    metadata={
                        "hub_id": hub_id,
                        "hub_name": hub_name,
                        "sender_count": sender_count,
                        "sub_min": sub_min,
                        "sub_max": sub_max
                    }
                )
                patterns.append(pattern)
        except Exception as e:
            logger.error(f"Error in fan-in smurfing detection: {str(e)}")

        # 2. Fan-Out Smurfing Query
        fan_out_query = """
        MATCH (source:Account)-[r:SENT]->(target:Account)
        WHERE r.amount >= $sub_min AND r.amount < $sub_max
        WITH source, count(DISTINCT target) AS target_count,
             collect(DISTINCT target.account_id) AS target_ids,
             collect(r.transaction_id) AS tx_ids,
             round(sum(r.amount) * 100.0) / 100.0 AS total_amount
        WHERE target_count >= $min_acc
        RETURN source.account_id AS source_id,
               source.customer_name AS source_name,
               target_count,
               target_ids,
               tx_ids,
               total_amount
        ORDER BY total_amount DESC
        """

        try:
            records = db.execute_read(fan_out_query, {
                "sub_min": float(sub_min),
                "sub_max": float(sub_max),
                "min_acc": int(min_acc)
            })
            for rec in records:
                source_id = rec.get("source_id")
                source_name = rec.get("source_name")
                target_count = rec.get("target_count", 0)
                target_ids = rec.get("target_ids", [])
                tx_ids = rec.get("tx_ids", [])
                total_amount = float(rec.get("total_amount", 0.0))
                pattern_id = f"PAT-SMURF-OUT-{source_id}"

                pattern = FlaggedPattern(
                    pattern_id=pattern_id,
                    pattern_type=SuspiciousPatternType.SMURFING_FAN_OUT,
                    severity=PatternSeverity.HIGH,
                    rule_name="Structuring / Smurfing (Fan-Out Dispersal)",
                    summary=f"Source account {source_id} ({source_name}) dispersed ${total_amount:,.2f} across {target_count} target accounts.",
                    explainability=(
                        f"Account {source_id} systematically dispersed ${total_amount:,.2f} into {target_count} recipient accounts "
                        f"in amounts narrowly structured beneath ${sub_max:,.2f}. "
                        f"Rapid fan-out of funds to disparate accounts is consistent with capital dispersion and laundering mules."
                    ),
                    recommended_action=(
                        "1. Restrict outgoing outbound transfers on source account. "
                        "2. Review IP address and geolocations of outgoing transaction requests."
                    ),
                    involved_accounts=[source_id] + target_ids,
                    involved_transactions=tx_ids,
                    total_amount=total_amount,
                    cypher_query_used=fan_out_query.strip(),
                    metadata={
                        "source_id": source_id,
                        "source_name": source_name,
                        "target_count": target_count,
                        "sub_min": sub_min,
                        "sub_max": sub_max
                    }
                )
                patterns.append(pattern)
        except Exception as e:
            logger.error(f"Error in fan-out smurfing detection: {str(e)}")

        return patterns

    @classmethod
    def run_all_detection(
        cls,
        large_threshold: Optional[float] = None,
        circular_min: Optional[int] = None,
        circular_max: Optional[int] = None,
        smurfing_min_acc: Optional[int] = None
    ) -> FraudDetectionReport:
        """Run all fraud detection algorithms and return aggregated findings."""
        start_time = time.time()
        patterns: List[FlaggedPattern] = []

        # 1. Circular
        circular_patterns = cls.detect_circular_transactions(
            min_depth=circular_min or settings.CIRCULAR_MIN_DEPTH,
            max_depth=circular_max or settings.CIRCULAR_MAX_DEPTH
        )
        patterns.extend(circular_patterns)

        # 2. Large Transactions
        large_patterns = cls.detect_large_transactions(
            threshold=large_threshold or settings.LARGE_TRANSACTION_THRESHOLD
        )
        patterns.extend(large_patterns)

        # 3. Smurfing
        smurfing_patterns = cls.detect_smurfing_structuring(
            min_accounts=smurfing_min_acc or settings.SMURFING_MIN_ACCOUNTS
        )
        patterns.extend(smurfing_patterns)

        # Sort patterns by severity
        severity_rank = {
            PatternSeverity.CRITICAL: 0,
            PatternSeverity.HIGH: 1,
            PatternSeverity.MEDIUM: 2,
            PatternSeverity.LOW: 3
        }
        patterns.sort(key=lambda p: (severity_rank.get(p.severity, 99), -p.total_amount))

        # Calculate metrics
        critical_count = sum(1 for p in patterns if p.severity == PatternSeverity.CRITICAL)
        high_count = sum(1 for p in patterns if p.severity == PatternSeverity.HIGH)
        med_count = sum(1 for p in patterns if p.severity == PatternSeverity.MEDIUM)
        low_count = sum(1 for p in patterns if p.severity == PatternSeverity.LOW)
        total_flagged_amount = round(sum(p.total_amount for p in patterns), 2)

        unique_involved_accounts = set()
        for p in patterns:
            unique_involved_accounts.update(p.involved_accounts)

        summary = DetectionReportSummary(
            total_patterns_detected=len(patterns),
            critical_severity_count=critical_count,
            high_severity_count=high_count,
            medium_severity_count=med_count,
            low_severity_count=low_count,
            total_flagged_amount=total_flagged_amount,
            total_accounts_involved=len(unique_involved_accounts)
        )

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
        now_str = datetime.now(timezone.utc).isoformat()

        return FraudDetectionReport(
            summary=summary,
            patterns=patterns,
            generated_at=now_str,
            execution_time_ms=elapsed_ms
        )
