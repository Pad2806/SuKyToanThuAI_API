"""
tasks/asset_worker.py
Background tasks — xử lý các công việc nặng ở chế độ bất đồng bộ (async).

Tại sao cần background tasks?
- Tìm ảnh từ Wikimedia + gọi AI có thể mất 5-15 giây
- Nếu xử lý đồng bộ → request timeout → FE báo lỗi
- Background task: nhận request ngay lập tức (202 Accepted),
  xử lý ngầm, FE có thể polling để lấy kết quả

Phase 1: Skeleton.
Phase 3+: Implement nếu cần async processing.
"""
import logging

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


def schedule_asset_generation(
    background_tasks: BackgroundTasks,
    job_id: str,
    scenes_data: dict,
) -> None:
    """
    Thêm việc generate ảnh vào hàng đợi background tasks của FastAPI.

    Args:
        background_tasks: FastAPI BackgroundTasks instance (inject từ endpoint)
        job_id:           ID để tracking job (sau này dùng để polling)
        scenes_data:      Dữ liệu scenes cần xử lý

    TODO (Phase 3): Implement _process_asset_generation_job.
    """
    background_tasks.add_task(_process_asset_generation_job, job_id, scenes_data)
    logger.info("Đã thêm job generate assets vào queue: job_id=%s", job_id)


async def _process_asset_generation_job(job_id: str, scenes_data: dict) -> None:
    """
    Hàm xử lý thật — chạy ngầm sau khi đã response 202 cho FE.

    TODO (Phase 3): Gọi asset_service.generate() và lưu kết quả.
    """
    logger.info("Bắt đầu xử lý job: %s", job_id)
    # TODO: Gọi asset_service và lưu kết quả vào Redis/DB để FE polling
    logger.info("Job hoàn thành: %s", job_id)
