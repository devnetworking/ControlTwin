import axiosInstance from "../lib/axios";

export async function getDatapoints(assetId) {
  const response = await axiosInstance.get("/datapoints", {
    params: { asset_id: assetId },
  });
  return response.data;
}

export async function createDatapoint(data) {
  const response = await axiosInstance.post("/datapoints", data);
  return response.data;
}

export async function queryTimeseries(payload = {}) {
  const dataPointIds = payload.data_point_ids ?? payload.datapoint_ids ?? [];
  const start = payload.start;
  const stop = payload.stop;
  const aggregate_window = payload.aggregate_window;
  const aggregate_fn = payload.aggregate_fn;

  if (!Array.isArray(dataPointIds) || dataPointIds.length === 0 || !start || !stop) {
    return [];
  }

  const response = await axiosInstance.post("/datapoints/query", {
    data_point_ids: dataPointIds,
    start,
    stop,
    aggregate_window,
    aggregate_fn,
  });
  return response.data;
}

export async function getLatestValue(dpId) {
  const response = await axiosInstance.get(`/datapoints/${dpId}/latest`);
  return response.data;
}
