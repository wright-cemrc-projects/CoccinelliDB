import { useEffect, useState } from "react";
import { App, Alert, Checkbox, Empty, Modal, Table, Tag, Tooltip, Typography } from "antd";
import axios from "axios";
import dayjs from "dayjs";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

interface MergeCandidate {
    id: number;
    start_date: string | null;
    end_date: string | null;
    notes: string | null;
    collection_count: number;
    person_count: number;
    has_locked_collections: boolean;
}

interface MergePlanPerson {
    person_id: number;
    name: string;
    onsite: boolean;
    role: string;
    hours: number;
    remote_access_level: string;
}

interface MergePlan {
    primary_id: number;
    other_ids: number[];
    start_date: string | null;
    end_date: string | null;
    notes: string | null;
    persons: MergePlanPerson[];
    collection_ids_to_move: number[];
    warnings: string[];
}

interface MergeSessionsModalProps {
    open: boolean;
    sessionId?: number;
    onCancel: () => void;
    /** Called after a successful merge — the modal's session is now the merged result. */
    onMerged: () => void;
}

/**
 * Finds other sessions on the same instrument that look like accidental
 * duplicates of this one (same day, or an overlapping time range), lets the
 * user pick which to fold in, and previews the merged result — combined time
 * range, concatenated notes, unioned participants (hours summed for anyone on
 * more than one session) — before committing. This session (the one the Edit
 * page was already open on) is always the surviving "primary"; the selected
 * others are deleted once their data has been moved over.
 */
export const MergeSessionsModal = ({ open, sessionId, onCancel, onMerged }: MergeSessionsModalProps) => {
    const { message } = App.useApp();
    const [candidates, setCandidates] = useState<MergeCandidate[]>([]);
    const [candidatesLoading, setCandidatesLoading] = useState(false);
    const [selectedIds, setSelectedIds] = useState<number[]>([]);
    const [plan, setPlan] = useState<MergePlan | null>(null);
    const [previewError, setPreviewError] = useState<string | null>(null);
    const [merging, setMerging] = useState(false);

    useEffect(() => {
        if (!open || !sessionId) return;
        setSelectedIds([]);
        setPlan(null);
        setCandidatesLoading(true);
        axios
            .get(`${API_URL}/instrumentsession/${sessionId}/merge_candidates`, { withCredentials: true })
            .then((response) => setCandidates(response.data?.candidates ?? []))
            .catch(() => setCandidates([]))
            .finally(() => setCandidatesLoading(false));
    }, [open, sessionId]);

    useEffect(() => {
        if (!open || !sessionId || selectedIds.length === 0) {
            setPlan(null);
            setPreviewError(null);
            return;
        }
        let cancelled = false;
        (async () => {
            try {
                const response = await axios.post(
                    `${API_URL}/instrumentsession/merge/preview`,
                    { primary_id: sessionId, other_ids: selectedIds },
                    { withCredentials: true }
                );
                if (!cancelled) {
                    setPlan(response.data);
                    setPreviewError(null);
                }
            } catch (error: any) {
                if (!cancelled) {
                    setPlan(null);
                    setPreviewError(error.response?.data?.error ?? "Could not preview the merge.");
                }
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [open, sessionId, selectedIds.join(",")]);

    const toggleSelected = (id: number, checked: boolean) => {
        setSelectedIds((prev) => (checked ? [...prev, id] : prev.filter((x) => x !== id)));
    };

    const handleMerge = async () => {
        if (!sessionId || selectedIds.length === 0) return;
        setMerging(true);
        try {
            const response = await axios.post(
                `${API_URL}/instrumentsession/merge`,
                { primary_id: sessionId, other_ids: selectedIds },
                { withCredentials: true }
            );
            message.success(response.data?.message ?? "Sessions merged successfully.");
            onMerged();
        } catch (error: any) {
            message.error(error.response?.data?.error ?? "Failed to merge sessions.");
        } finally {
            setMerging(false);
        }
    };

    const formatRange = (start: string | null, end: string | null) =>
        start
            ? `${dayjs(start).format("YYYY-MM-DD h:mm A")} – ${end ? dayjs(end).format("h:mm A") : "?"}`
            : "no dates";

    return (
        <Modal
            open={open}
            title="Merge duplicate sessions"
            onCancel={onCancel}
            onOk={handleMerge}
            okText={`Merge${selectedIds.length ? ` (${selectedIds.length})` : ""}`}
            okButtonProps={{ disabled: selectedIds.length === 0 || !plan, loading: merging }}
            width={720}
            destroyOnClose
        >
            <Typography.Paragraph type="secondary">
                This session will absorb whichever sessions you select below: its time range widens
                to cover all of them, their notes are appended to its own, participants are combined
                (hours summed for anyone on more than one), and all of their collections move over.
                The selected sessions are then deleted.
            </Typography.Paragraph>

            <Typography.Text strong>Sessions on this instrument that might be duplicates</Typography.Text>
            {candidatesLoading ? (
                <Typography.Paragraph type="secondary">Looking for candidates…</Typography.Paragraph>
            ) : candidates.length === 0 ? (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No other sessions on this instrument overlap or share this session's day."
                    style={{ margin: "16px 0" }}
                />
            ) : (
                <Table
                    dataSource={candidates}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    style={{ marginTop: 8, marginBottom: 16 }}
                >
                    <Table.Column
                        title=""
                        width={40}
                        render={(_, record: MergeCandidate) => (
                            <Checkbox
                                checked={selectedIds.includes(record.id)}
                                onChange={(e) => toggleSelected(record.id, e.target.checked)}
                            />
                        )}
                    />
                    <Table.Column dataIndex="id" title="ID" width={70} />
                    <Table.Column
                        title="Range"
                        render={(_, record: MergeCandidate) => formatRange(record.start_date, record.end_date)}
                    />
                    <Table.Column dataIndex="collection_count" title="Collections" width={100} />
                    <Table.Column dataIndex="person_count" title="Persons" width={90} />
                    <Table.Column
                        dataIndex="notes"
                        title="Notes"
                        render={(value: string | null) =>
                            value ? (
                                <Typography.Text ellipsis={{ tooltip: value }} style={{ maxWidth: 200, display: "inline-block" }}>
                                    {value}
                                </Typography.Text>
                            ) : (
                                "—"
                            )
                        }
                    />
                    <Table.Column
                        title=""
                        render={(_, record: MergeCandidate) =>
                            record.has_locked_collections ? (
                                <Tooltip title="Has finalized collection(s). Merging moves them onto this session but keeps them finalized.">
                                    <Tag color="gold">Finalized collection</Tag>
                                </Tooltip>
                            ) : null
                        }
                    />
                </Table>
            )}

            {previewError && <Alert type="warning" showIcon message={previewError} style={{ marginBottom: 16 }} />}

            {plan && (
                <>
                    <Typography.Text strong>Preview of the merged session</Typography.Text>
                    <div style={{ marginTop: 8, marginBottom: 16 }}>
                        {plan.warnings.map((warning, i) => (
                            <Alert key={i} type="warning" showIcon message={warning} style={{ marginBottom: 8 }} />
                        ))}

                        <Typography.Paragraph>
                            <strong>New range: </strong>
                            {formatRange(plan.start_date, plan.end_date)}
                        </Typography.Paragraph>

                        <Typography.Paragraph>
                            <strong>{plan.collection_ids_to_move.length}</strong> collection(s) will move onto
                            this session.
                        </Typography.Paragraph>

                        <Typography.Text strong>Participants after merge</Typography.Text>
                        <Table
                            dataSource={plan.persons}
                            rowKey="person_id"
                            pagination={false}
                            size="small"
                            style={{ marginTop: 8, marginBottom: 16 }}
                        >
                            <Table.Column dataIndex="name" title="Person" />
                            <Table.Column dataIndex="role" title="Role" />
                            <Table.Column dataIndex="hours" title="Hours" width={80} />
                        </Table>

                        <Typography.Text strong>Combined notes</Typography.Text>
                        <div
                            style={{
                                marginTop: 8,
                                padding: 8,
                                maxHeight: 160,
                                overflowY: "auto",
                                whiteSpace: "pre-wrap",
                                border: "1px solid rgba(0,0,0,0.1)",
                                borderRadius: 4,
                                fontSize: 12,
                            }}
                        >
                            {plan.notes || <Typography.Text type="secondary">(no notes)</Typography.Text>}
                        </div>
                    </div>
                </>
            )}
        </Modal>
    );
};
