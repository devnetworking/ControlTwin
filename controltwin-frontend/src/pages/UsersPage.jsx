import { useState } from "react";
import axios from "axios";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../lib/axios";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { Button } from "../components/ui/button";
import { Dialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { ROLE_LABELS } from "../constants/ics";
import { formatDate } from "../lib/utils";
import EmptyState from "../components/ui/EmptyState";
import { useAuth } from "../hooks/useAuth";

function roleColor(role) {
  return ROLE_LABELS[role]?.color || "#6B7280";
}

export default function UsersPage() {
  const { role } = useAuth();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    full_name: "",
    role: "viewer"
  });
  const [errorMessage, setErrorMessage] = useState("");

  const { data, refetch } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const meResponse = await axiosInstance.get("/users/me");
      const me = meResponse.data;
      return me ? [me] : [];
    },
    enabled: role === "admin" || role === "super_admin"
  });

  const users = Array.isArray(data) ? data : data?.items || [];

  async function addUser(e) {
    e.preventDefault();
    if (!form.username || !form.email || !form.password || !form.full_name) return;

    setErrorMessage("");
    try {
      await axiosInstance.post("/users", form);
      setOpen(false);
      setForm({ username: "", email: "", password: "", full_name: "", role: "viewer" });
      refetch();
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setErrorMessage("Username or email already exists.");
      } else {
        setErrorMessage("Unable to create user. Please try again.");
      }
    }
  }

  if (!(role === "admin" || role === "super_admin")) {
    return <div className="text-ot-red">Permission denied.</div>;
  }

  if (!users.length) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Users</h1>
        <Button
          onClick={() => {
            setErrorMessage("");
            setOpen(true);
          }}
        >
          Add User
        </Button>
        <EmptyState title="No users" description="No users found in this environment." />
        <Dialog open={open} onOpenChange={setOpen} title="Add User">
          <UserForm form={form} setForm={setForm} onSubmit={addUser} errorMessage={errorMessage} />
        </Dialog>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Users</h1>
        <Button
          onClick={() => {
            setErrorMessage("");
            setOpen(true);
          }}
        >
          Add User
        </Button>
      </div>

      <div className="rounded-lg border border-ot-border bg-ot-card">
        <Table>
          <THead>
            <TR>
              <TH>Username</TH>
              <TH>Email</TH>
              <TH>Full Name</TH>
              <TH>Role</TH>
              <TH>Active</TH>
              <TH>Last Login</TH>
            </TR>
          </THead>
          <TBody>
            {users.map((u) => (
              <TR key={u.id}>
                <TD>{u.username}</TD>
                <TD>{u.email}</TD>
                <TD>{u.full_name}</TD>
                <TD>
                  <span className="rounded px-2 py-0.5 text-xs text-black" style={{ background: roleColor(u.role) }}>
                    {ROLE_LABELS[u.role]?.label || u.role}
                  </span>
                </TD>
                <TD>{u.is_active ? "🟢" : "🔴"}</TD>
                <TD>{formatDate(u.last_login)}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>

      <Dialog open={open} onOpenChange={setOpen} title="Add User">
        <UserForm form={form} setForm={setForm} onSubmit={addUser} errorMessage={errorMessage} />
      </Dialog>
    </div>
  );
}

function UserForm({ form, setForm, onSubmit, errorMessage }) {
  return (
    <form className="space-y-3" onSubmit={onSubmit}>
      <Input
        placeholder="Username"
        value={form.username}
        onChange={(e) => setForm((s) => ({ ...s, username: e.target.value }))}
        required
      />
      <Input
        placeholder="Email"
        value={form.email}
        onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))}
        required
      />
      <Input
        type="password"
        placeholder="Password"
        value={form.password}
        onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))}
        required
      />
      <Input
        placeholder="Full name"
        value={form.full_name}
        onChange={(e) => setForm((s) => ({ ...s, full_name: e.target.value }))}
        required
      />
      <Select value={form.role} onChange={(e) => setForm((s) => ({ ...s, role: e.target.value }))}>
        {Object.entries(ROLE_LABELS).map(([key, val]) => (
          <option key={key} value={key}>
            {val.label}
          </option>
        ))}
      </Select>
      <div className="text-xs text-gray-300">
        {ROLE_LABELS[form.role]?.description}
      </div>
      {errorMessage ? (
        <div className="text-sm text-ot-red">{errorMessage}</div>
      ) : null}
      <Button type="submit" className="w-full">Create User</Button>
    </form>
  );
}
