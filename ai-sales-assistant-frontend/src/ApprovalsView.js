import React, { useState, useEffect, useCallback } from "react";
import { fetchApprovals, resolveApproval } from "./services/api";

export default function ApprovalsView() {
    const [approvals, setApprovals] = useState([]);
    const [loading, setLoading] = useState(false);
    const [resolving, setResolving] = useState(null); // id of record being resolved

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await fetchApprovals();
            setApprovals(data || []);
        } catch (e) {
            console.error("Failed to fetch approvals:", e.message);
        }
        setLoading(false);
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleResolve = async (id, approved) => {
        setResolving(id);
        try {
            await resolveApproval(id, approved);
            // Remove from list or refresh
            setApprovals(prev => prev.filter(a => a.id !== id));
        } catch (e) {
            alert(`Error resolving approval: ${e.message}`);
        }
        setResolving(null);
    };

    return (
        <div className="approvals-wrapper">
            <div className="approvals-header">
                <div>
                    <h2>⚖️ Approvals</h2>
                    <p className="leads-total">Sensitive actions requiring human confirmation.</p>
                </div>
                <button className="refresh-btn" onClick={load} disabled={loading}>
                    {loading ? "Loading…" : "↻ Refresh"}
                </button>
            </div>

            {loading && <div className="loading-bar" />}

            {approvals.length === 0 && !loading ? (
                <div className="leads-empty">
                    <span style={{ fontSize: 40 }}>🛡️</span>
                    <p>No pending approvals. Your AI is being well-behaved!</p>
                    <p className="leads-empty-hint">Try: <em>"Delete lead test@example.com"</em> in Chat.</p>
                </div>
            ) : (
                <div className="approvals-list">
                    {approvals.map(req => (
                        <div key={req.id} className="approval-card">
                            <div className="approval-badge">PENDING</div>
                            <div className="approval-content">
                                <div className="approval-main">
                                    <span className="approval-intent">{req.intent.replace("_", " ")}</span>
                                    <span className="approval-time">{new Date(req.created_at).toLocaleString()}</span>
                                </div>

                                <div className="approval-details">
                                    {req.intent === "delete_lead" && (
                                        <p>Delete lead: <strong>{req.payload.entities?.email}</strong></p>
                                    )}
                                    {req.intent === "apply_discount" && (
                                        <p>Apply discount <strong>{req.payload.entities?.discount}</strong> to <strong>{req.payload.entities?.email}</strong></p>
                                    )}
                                    <pre className="approval-json">{JSON.stringify(req.payload.entities, null, 2)}</pre>
                                </div>
                            </div>

                            <div className="approval-actions">
                                <button
                                    className="btn-approve"
                                    onClick={() => handleResolve(req.id, true)}
                                    disabled={!!resolving}
                                >
                                    {resolving === req.id ? "..." : "Approve ✅"}
                                </button>
                                <button
                                    className="btn-reject"
                                    onClick={() => handleResolve(req.id, false)}
                                    disabled={!!resolving}
                                >
                                    {resolving === req.id ? "..." : "Reject ❌"}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
