import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createAsset, getAssets, updateAsset } from "../api/assets";

export function useAssets(filters = {}) {
  return useQuery({
    queryKey: ["assets", filters],
    queryFn: () => getAssets(filters),
    staleTime: 60000
  });
}

export function useCreateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createAsset,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assets"] })
  });
}

export function useUpdateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }) => updateAsset(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assets"] })
  });
}
