import api from "@/lib/api";

export const useQuarantineActions = (onSuccess: () => void) => {
  const handleRelease = async (id: number) => {
    try {
      await api.post("/api/quarantine/release/", { id });
      onSuccess();
    } catch (err: any) {
      console.error("Release error:", err);
      alert("Failed to release email");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to permanently delete this email?")) {
      return;
    }
    try {
      await api.post("/api/quarantine/delete/", { id });
      onSuccess();
    } catch (err: any) {
      console.error("Delete error:", err);
      alert("Failed to delete email");
    }
  };

  return { handleRelease, handleDelete };
};

