"""ControlTwin AI — Predictive Maintenance Scheduler
APScheduler jobs for periodic ML tasks.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("controltwin.scheduler")


class PredictiveScheduler:
    def __init__(self, predictor, baseline_calculator, model_trainer):
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.predictor = predictor
        self.baseline = baseline_calculator
        self.trainer = model_trainer
        self._setup_jobs()

    def _setup_jobs(self):
        # Job 1: Compute RUL for ALL critical assets — daily at 02:00 UTC
        self.scheduler.add_job(
            self._compute_rul_all_assets,
            CronTrigger(hour=2, minute=0),
            id="daily_rul_computation",
            name="Daily RUL Computation",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        # Job 2: Refresh baselines for active data points — every 6 hours
        self.scheduler.add_job(
            self._update_baselines,
            IntervalTrigger(hours=6),
            id="baseline_refresh",
            name="Baseline Refresh",
            replace_existing=True,
        )

        # Job 3: Retrain Isolation Forest models — weekly Sunday 03:00 UTC
        self.scheduler.add_job(
            self._retrain_ml_models,
            CronTrigger(day_of_week="sun", hour=3, minute=0),
            id="weekly_model_retrain",
            name="Weekly ML Model Retrain",
            replace_existing=True,
            misfire_grace_time=7200,
        )

        # Job 4: Generate daily maintenance report — daily at 06:00 UTC
        self.scheduler.add_job(
            self._generate_maintenance_report,
            CronTrigger(hour=6, minute=0),
            id="daily_maintenance_report",
            name="Daily Maintenance Report",
            replace_existing=True,
        )

    async def _compute_rul_all_assets(self):
        """
        Query all active critical assets from DB, call predictor.compute_rul(asset_id),
        store results, and log summary.
        """
        try:
            assets = []
            if hasattr(self.predictor, "get_active_critical_assets"):
                assets = await self.predictor.get_active_critical_assets()

            processed = 0
            for asset in assets:
                asset_id = asset.get("id") if isinstance(asset, dict) else asset
                result = await self.predictor.compute_rul(asset_id)
                if hasattr(self.predictor, "store_rul_result"):
                    await self.predictor.store_rul_result(asset_id, result)
                processed += 1

            logger.info("Daily RUL computation completed for %s assets", processed)
        except Exception as exc:
            logger.exception("RUL computation job failed: %s", exc)

    async def _update_baselines(self):
        """
        Get active data_point_ids from DB, call baseline.get_baseline(dp_id, force_refresh=True),
        and log count updated.
        """
        try:
            data_point_ids = []
            if hasattr(self.baseline, "get_active_data_point_ids"):
                data_point_ids = await self.baseline.get_active_data_point_ids()

            updated = 0
            for dp_id in data_point_ids:
                await self.baseline.get_baseline(dp_id, force_refresh=True)
                updated += 1

            logger.info("Baseline refresh completed for %s data points", updated)
        except Exception as exc:
            logger.exception("Baseline refresh job failed: %s", exc)

    async def _retrain_ml_models(self):
        """
        Get assets with >1000 data points (last 30d), call trainer.retrain(asset_id),
        and log metrics.
        """
        try:
            assets = []
            if hasattr(self.trainer, "get_assets_for_retraining"):
                assets = await self.trainer.get_assets_for_retraining(
                    min_points=1000,
                    lookback_days=30,
                )

            retrained = 0
            for asset in assets:
                asset_id = asset.get("id") if isinstance(asset, dict) else asset
                metrics = await self.trainer.retrain(asset_id)
                retrained += 1
                logger.info("Retrained asset %s with metrics: %s", asset_id, metrics)

            logger.info("Weekly model retrain completed for %s assets", retrained)
        except Exception as exc:
            logger.exception("Model retrain job failed: %s", exc)

    async def _generate_maintenance_report(self):
        """
        Query RUL results from DB and generate daily maintenance report.
        """
        try:
            rul_results = []
            if hasattr(self.predictor, "get_latest_rul_results"):
                rul_results = await self.predictor.get_latest_rul_results()

            if hasattr(self.predictor, "generate_maintenance_report"):
                report = await self.predictor.generate_maintenance_report(rul_results)
                logger.info("Daily maintenance report generated: %s", report)
            else:
                logger.info(
                    "Daily maintenance report prepared from %s RUL entries",
                    len(rul_results),
                )
        except Exception as exc:
            logger.exception("Maintenance report job failed: %s", exc)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("PredictiveScheduler started")

    def shutdown(self, wait: bool = False):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("PredictiveScheduler stopped")
