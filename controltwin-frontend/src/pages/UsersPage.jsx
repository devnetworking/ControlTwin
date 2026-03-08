import { useMemo, useState } from "react";
import axios from "axios";
import { useQuery } from "@tanstack/react-query";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { Button } from "../components/ui/button";
import { Dialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { ROLE_LABELS } from "../constants/ics";
import { formatDate } from "../lib/utils";
import EmptyState from "../components/ui/EmptyState";
import { useAuth } from "../hooks/useAuth";
import { activateUser, createUser, deactivateUser, deleteUser, listUsers, updateUser } from "../api/users";
import { useLang } from "../lang";

function roleColor(role) {
  return ROLE_LABELS[role]?.color || "#6B7280";
}

const emptyCreateForm = {
  username: "",
  email: "",
  password: "",
  role: "viewer"
};

const emptyEditForm = {
  email: "",
  role: "viewer"
};

export default function UsersPage() {
  const { t } = useLang();
  const { role } = useAuth();
  const canManageUsers = role === "admin" || role === "super_admin";

  const [openCreate, setOpenCreate] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [editForm, setEditForm] = useState(emptyEditForm);

  const [errorMessage, setErrorMessage] = useState("");
  const [busyUserId, setBusyUserId] = useState("");

  const { data, refetch, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: listUsers,
    enabled: canManageUsers
  });

  const users = useMemo(() => (Array.isArray(data) ? data : []), [data]);

  async function handleCreateUser(e) {
    e.preventDefault();
    if (!createForm.username || !createForm.email || !createForm.password) return;

    setErrorMessage("");
    try {
      await createUser(createForm);
      setOpenCreate(false);
      setCreateForm(emptyCreateForm);
      await refetch();
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setErrorMessage("Username or email already exists.");
      } else {
        setErrorMessage("Unable to create user. Please try again.");
      }
    }
  }

  function openEditDialog(user) {
    setSelectedUser(user);
    setEditForm({
      email: user.email || "",
      role: user.role || "viewer"
    });
    setErrorMessage("");
    setOpenEdit(true);
  }

  async function handleEditUser(e) {
    e.preventDefault();
    if (!selectedUser) return;
    setErrorMessage("");

    try {
      await updateUser(selectedUser.id, {
        email: editForm.email,
        role: editForm.role
      });
      setOpenEdit(false);
      setSelectedUser(null);
      await refetch();
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setErrorMessage("Email already exists.");
      } else {
        setErrorMessage("Unable to update user.");
      }
    }
  }

  async function handleToggleActive(user) {
    setBusyUserId(user.id);
    setErrorMessage("");
    try {
      if (user.is_active) {
        await deactivateUser(user.id);
      } else {
        await activateUser(user.id);
      }
      await refetch();
    } catch {
      setErrorMessage("Unable to change user status.");
    } finally {
      setBusyUserId("");
    }
  }

  async function handleDelete(user) {
    const ok = window.confirm(`Delete user "${user.username}"? This action cannot be undone.`);
    if (!ok) return;

    setBusyUserId(user.id);
    setErrorMessage("");
    try {
      await deleteUser(user.id);
      await refetch();
    } catch {
      setErrorMessage("Unable to delete user.");
    } finally {
      setBusyUserId("");
    }
  }

  if (!canManageUsers) {
    return <div className="text-ot-red">Permission denied.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t("users.title")}</h1>
        <Button
          onClick={() => {
            setErrorMessage("");
            setOpenCreate(true);
          }}
        >
          {t("users.addUser")}
        </Button>
      </div>

      {errorMessage ? <div className="text-sm text-ot-red">{errorMessage}</div> : null}

      {!isLoading && !users.length ? (
        <EmptyState title={t("users.noUsers")} description={t("common.noData")} />
      ) : null}

      <div className="rounded-lg border border-ot-border bg-ot-card">
        <Table>
          <THead>
            <TR>
              <TH>{t("users.username")}</TH>
              <TH>{t("users.email")}</TH>
              <TH>{t("users.role")}</TH>
              <TH>{t("users.status")}</TH>
              <TH>{t("users.lastLogin")}</TH>
              <TH>{t("users.actions")}</TH>
            </TR>
          </THead>
          <TBody>
            {users.map((u) => (
              <TR key={u.id}>
                <TD>{u.username}</TD>
                <TD>{u.email}</TD>
                <TD>
                  <span className="rounded px-2 py-0.5 text-xs text-black" style={{ background: roleColor(u.role) }}>
                    {ROLE_LABELS[u.role]?.label || u.role}
                  </span>
                </TD>
                <TD>{u.is_active ? "🟢" : "🔴"}</TD>
                <TD>{formatDate(u.last_login)}</TD>
                <TD>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEditDialog(u)}>
                      {t("common.edit")}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busyUserId === u.id}
                      onClick={() => handleToggleActive(u)}
                    >
                      {u.is_active ? t("users.inactive") : t("users.active")}
                    </Button>
                    <Button size="sm" variant="destructive" disabled={busyUserId === u.id} onClick={() => handleDelete(u)}>
                      {t("common.delete")}
                    </Button>
                  </div>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>

      <Dialog open={openCreate} onOpenChange={setOpenCreate} title={t("users.addUser")}>
        <CreateUserForm
          form={createForm}
          setForm={setCreateForm}
          onSubmit={handleCreateUser}
        />
      </Dialog>

      <Dialog open={openEdit} onOpenChange={setOpenEdit} title={t("common.edit")}>
        <EditUserForm form={editForm} setForm={setEditForm} onSubmit={handleEditUser} />
      </Dialog>
    </div>
  );
}

function CreateUserForm({ form, setForm, onSubmit }) {
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
      <Select value={form.role} onChange={(e) => setForm((s) => ({ ...s, role: e.target.value }))}>
        {Object.entries(ROLE_LABELS).map(([key, val]) => (
          <option key={key} value={key}>
            {val.label}
          </option>
        ))}
      </Select>
      <div className="text-xs text-gray-300">{ROLE_LABELS[form.role]?.description}</div>
      <Button type="submit" className="w-full">
        Create User
      </Button>
    </form>
  );
}

function EditUserForm({ form, setForm, onSubmit }) {
  return (
    <form className="space-y-3" onSubmit={onSubmit}>
      <Input
        placeholder="Email"
        value={form.email}
        onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))}
        required
      />
      <Select value={form.role} onChange={(e) => setForm((s) => ({ ...s, role: e.target.value }))}>
        {Object.entries(ROLE_LABELS).map(([key, val]) => (
          <option key={key} value={key}>
            {val.label}
          </option>
        ))}
      </Select>
      <div className="text-xs text-gray-300">{ROLE_LABELS[form.role]?.description}</div>
      <Button type="submit" className="w-full">
        Save Changes
      </Button>
    </form>
  );
}
