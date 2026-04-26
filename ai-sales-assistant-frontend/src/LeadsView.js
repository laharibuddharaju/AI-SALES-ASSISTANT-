import React, { useState, useEffect, useCallback } from "react";
import { fetchLeads, createLead, updateLead, deleteLead, syncLeads } from "./services/api";

const STATUS_COLORS = {
    new: { bg: "#1e3a5f", text: "#60a5fa" },
    qualified: { bg: "#14532d", text: "#4ade80" },
    contacted: { bg: "#3b1f5e", text: "#c084fc" },
    closed: { bg: "#1c3128", text: "#34d399" },
    lost: { bg: "#4c1d1d", text: "#f87171" },
    unknown: { bg: "#1e2536", text: "#94a3b8" },
};

const StatusBadge = ({ status }) => {
    const s = status?.toLowerCase() || "unknown";
    const c = STATUS_COLORS[s] || STATUS_COLORS.unknown;
    return (
        <span style={{
            padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
            background: c.bg, color: c.text, textTransform: "capitalize",
        }}>{s}</span>
    );
};

export default function LeadsView() {
    const [leads, setLeads] = useState([]);
    const [total, setTotal] = useState(0);
    const [totalPages, setTotalPages] = useState(1);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(25);
    const [search, setSearch] = useState("");
    const [statusFilter, setStatus] = useState("");
    const [loading, setLoading] = useState(false);
    const [searchInput, setSearchInput] = useState("");

    // Modals
    const [showModal, setShowModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [editingLead, setEditingLead] = useState(null);
    const [deletingId, setDeletingId] = useState(null);
    const [formData, setFormData] = useState({ email: "", name: "", company: "", phone: "", status: "new", deal_value: 0, product_code: "" });
    const [submitting, setSubmitting] = useState(false);
    const [syncing, setSyncing] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetchLeads({ page, limit, status: statusFilter, search });
            setLeads(res.leads || []);
            setTotal(res.total_count || 0);
            setTotalPages(res.total_pages || 1);
        } catch (e) {
            console.error("Failed to fetch leads:", e.message);
        }
        setLoading(false);
    }, [page, limit, statusFilter, search]);

    useEffect(() => { load(); }, [load]);

    const handleSearch = (e) => {
        if (e.key === "Enter" || e.type === "click") {
            setSearch(searchInput);
            setPage(1);
        }
    };

    const handleExport = () => {
        if (!leads.length) return;
        const headers = ["Email", "Name", "Company", "Phone", "Product Code", "Status", "Deal Value", "Source", "Created"];
        const rows = leads.map(l => [
            l.email, l.name || "", l.company || "", l.phone || "",
            l.product_code || "", l.status, l.deal_value || 0, l.source, l.created_at,
        ]);
        const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(",")).join("\n");
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = Object.assign(document.createElement("a"), { href: url, download: "leads.csv" });
        a.click(); URL.revokeObjectURL(url);
    };

    const handleSync = async () => {
        setSyncing(true);
        try {
            const res = await syncLeads();
            alert(`CRM Sync Complete: ${res.synced} synced, ${res.failed} failed.`);
            load();
        } catch (err) {
            alert(err.message);
        }
        setSyncing(false);
    };

    const openAddModal = () => {
        setEditingLead(null);
        setFormData({ email: "", name: "", company: "", phone: "", status: "new", deal_value: 0, product_code: "" });
        setShowModal(true);
    };

    const openEditModal = (lead) => {
        setEditingLead(lead);
        setFormData({
            email: lead.email,
            name: lead.name || "",
            company: lead.company || "",
            phone: lead.phone || "",
            status: lead.status || "new",
            deal_value: lead.deal_value || 0,
            product_code: lead.product_code || "",
        });
        setShowModal(true);
    };

    const confirmDelete = (id) => {
        setDeletingId(id);
        setShowDeleteModal(true);
    };

    const handleDelete = async () => {
        setSubmitting(true);
        try {
            await deleteLead(deletingId);
            setShowDeleteModal(false);
            load();
        } catch (err) {
            alert(err.message);
        }
        setSubmitting(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            if (editingLead) {
                await updateLead(editingLead.id, formData);
            } else {
                await createLead(formData);
            }
            setShowModal(false);
            load();
        } catch (err) {
            alert(err.message);
        }
        setSubmitting(false);
    };

    return (
        <div className="leads-wrapper">
            <div className="leads-header">
                <div>
                    <h2>👤 Leads Management</h2>
                    <p className="leads-total">{total} lead{total !== 1 ? "s" : ""} total</p>
                </div>
                <div style={{ display: "flex", gap: "10px" }}>
                    <button className="sync-btn" onClick={handleSync} disabled={syncing}>
                        {syncing ? "Syncing..." : "🔄 Sync CRM"}
                    </button>
                    <button className="export-btn" onClick={openAddModal}>+ Add Lead</button>
                    <button id="btn-export-csv" className="export-btn" onClick={handleExport} disabled={!leads.length}>
                        📤 Export CSV
                    </button>
                </div>
            </div>

            <div className="leads-filters">
                <div className="search-box">
                    <input
                        id="leads-search"
                        className="leads-search"
                        placeholder="Search email, name, company, product code…"
                        value={searchInput}
                        onChange={e => setSearchInput(e.target.value)}
                        onKeyDown={handleSearch}
                    />
                    <button id="btn-search" className="search-btn" onClick={handleSearch}>🔍</button>
                </div>

                <select
                    id="leads-status-filter"
                    className="status-filter"
                    value={statusFilter}
                    onChange={e => { setStatus(e.target.value); setPage(1); }}
                >
                    <option value="">All</option>
                    {["new", "contacted", "qualified", "closed", "lost"].map(s => (
                        <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                    ))}
                </select>

                <button id="btn-refresh-leads" className="refresh-btn" onClick={() => { load(); }} disabled={loading}>
                    {loading ? "Loading…" : "↻ Refresh"}
                </button>
            </div>

            {loading && <div className="loading-bar" />}

            {leads.length === 0 && !loading ? (
                <div className="leads-empty">
                    <span>🔍</span>
                    <p>No leads found. Create some via Chat!</p>
                </div>
            ) : (
                <div className="table-scroll">
                    <table className="leads-table">
                        <thead>
                            <tr>
                                <th>Email</th>
                                <th>Name / Phone</th>
                                <th>Company</th>
                                <th>Product Code</th>
                                <th>Status</th>
                                <th>Value</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {leads.map(l => (
                                <tr key={l.id} className="lead-row">
                                    <td className="lead-email">{l.email}</td>
                                    <td>
                                        <div>{l.name || <span className="muted">—</span>}</div>
                                        <div className="muted" style={{ fontSize: "11px" }}>{l.phone}</div>
                                    </td>
                                    <td>{l.company || <span className="muted">—</span>}</td>
                                    <td>
                                        {l.product_code
                                            ? <span style={{ fontFamily: "monospace", fontSize: "12px", background: "#1e2a3a", color: "#7dd3fc", padding: "2px 8px", borderRadius: 4 }}>{l.product_code}</span>
                                            : <span className="muted">—</span>}
                                    </td>
                                    <td><StatusBadge status={l.status} /></td>
                                    <td style={{ fontWeight: 600 }}>
                                        {l.deal_value ? `$${Number(l.deal_value).toLocaleString()}` : "$0"}
                                    </td>
                                    <td className="muted">{l.created_at}</td>
                                    <td>
                                        <div style={{ display: "flex", gap: "8px" }}>
                                            <button className="row-action" onClick={() => openEditModal(l)} title="Edit">✏️</button>
                                            <button className="row-action delete" onClick={() => confirmDelete(l.id)} title="Delete">🗑️</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="pagination-wrapper">
                <div className="rows-per-page">
                    <label>Rows per page:</label>
                    <select value={limit} onChange={e => { setLimit(Number(e.target.value)); setPage(1); }}>
                        <option value={10}>10</option>
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                    </select>
                </div>

                <div className="pagination">
                    <button id="btn-prev" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Prev</button>

                    <div className="page-numbers">
                        {[...Array(totalPages)].map((_, i) => {
                            const p = i + 1;
                            // Show first, last, and current ± 1
                            if (p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)) {
                                return (
                                    <button
                                        key={p}
                                        className={`page-num ${page === p ? "active" : ""}`}
                                        onClick={() => setPage(p)}
                                    >
                                        {p}
                                    </button>
                                );
                            } else if (p === page - 2 || p === page + 2) {
                                return <span key={p} className="muted">...</span>;
                            }
                            return null;
                        })}
                    </div>

                    <button id="btn-next" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Next →</button>
                </div>
            </div>

            {/* ── Add/Edit Modal ────────────────────────────────────────────────── */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-card" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>{editingLead ? "Edit Lead" : "Add New Lead"}</h3>
                            <button className="close-btn" onClick={() => setShowModal(false)}>&times;</button>
                        </div>
                        <form onSubmit={handleSubmit} className="modal-form">
                            <div className="form-group">
                                <label>Email Address *</label>
                                <input
                                    type="email" required
                                    disabled={!!editingLead}
                                    value={formData.email}
                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Full Name</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Company</label>
                                    <input
                                        type="text"
                                        value={formData.company}
                                        onChange={e => setFormData({ ...formData, company: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Phone</label>
                                    <input
                                        type="text"
                                        value={formData.phone}
                                        onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Product Code</label>
                                    <input
                                        type="text"
                                        maxLength={20}
                                        placeholder="Enter product code"
                                        value={formData.product_code}
                                        pattern="[A-Za-z0-9]*"
                                        title="Alphanumeric only, max 20 characters"
                                        onChange={e => {
                                            const val = e.target.value.replace(/[^A-Za-z0-9]/g, "");
                                            setFormData({ ...formData, product_code: val });
                                        }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Status</label>
                                    <select
                                        value={formData.status}
                                        onChange={e => setFormData({ ...formData, status: e.target.value })}
                                    >
                                        <option value="new">New</option>
                                        <option value="qualified">Qualified</option>
                                        <option value="contacted">Contacted</option>
                                        <option value="closed">Closed</option>
                                        <option value="lost">Lost</option>
                                    </select>
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Deal Value ($)</label>
                                <input
                                    type="number"
                                    value={formData.deal_value}
                                    onChange={e => setFormData({ ...formData, deal_value: Number(e.target.value) })}
                                />
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn-cancel" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn-save" disabled={submitting}>
                                    {submitting ? "Saving..." : "Save Lead"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ── Delete Confirmation Modal ─────────────────────────────────────── */}
            {showDeleteModal && (
                <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
                    <div className="modal-card small" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Confirm Deletion</h3>
                            <button className="close-btn" onClick={() => setShowDeleteModal(false)}>&times;</button>
                        </div>
                        <div className="modal-body">
                            <p>Are you sure you want to delete this lead? This action cannot be undone and will not sync back to CRM (it is a local purge).</p>
                        </div>
                        <div className="modal-footer">
                            <button className="btn-cancel" onClick={() => setShowDeleteModal(false)}>Cancel</button>
                            <button className="btn-delete" onClick={handleDelete} disabled={submitting}>
                                {submitting ? "Deleting..." : "Delete Permanently"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
