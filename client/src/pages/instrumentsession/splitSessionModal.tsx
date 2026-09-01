import { useEffect, useState } from "react";
import { App, Alert, Form, Input, Modal, Radio, Table, TimePicker, Typography } from "antd";
import axios from "axios";
import dayjs, { Dayjs } from "dayjs";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

const DEFAULT_DAY_START = dayjs().hour(9).minute(0).second(0);

type SplitMode = "day" | "collections";

interface SplitRange {
    start_date: string;
    end_date: string;
}

interface SplitSessionModalProps {
    open: boolean;
    sessionId?: number;
    /** Number of collections on the session that have a start_date, for the by-collection mode. */
    datedCollectionCount: number;
    onCancel: () => void;
    /** Called after a successful split, with the ids of the resulting sessions. */
    onSplit: (sessionIds: number[], sessionGroupId: number) => void;
}

/**
 * Asks how a multi-day session should be broken up, then splits it.
 *
 * In "day" mode the day boundary is a clock time (9:00 AM by default): every
 * occurrence of that time inside the session starts a new day. The resulting
 * sessions are contiguous — each ends where the next begins — so the block still
 * covers the original range. The preview table is fetched from the server so what
 * is shown is exactly what the split will do.
 */
export const SplitSessionModal = ({
    open,
    sessionId,
    datedCollectionCount,
    onCancel,
    onSplit,
}: SplitSessionModalProps) => {
    const { message } = App.useApp();
    const [mode, setMode] = useState<SplitMode>("day");
    const [dayStart, setDayStart] = useState<Dayjs | null>(DEFAULT_DAY_START);
    const [groupName, setGroupName] = useState("");
    const [ranges, setRanges] = useState<SplitRange[]>([]);
    const [previewError, setPreviewError] = useState<string | null>(null);
    const [splitting, setSplitting] = useState(false);

    useEffect(() => {
        if (!open || mode !== "day" || !sessionId || !dayStart) {
            return;
        }
        let cancelled = false;
        (async () => {
            try {
                const response = await axios.post(
                    `${API_URL}/instrumentsession/${sessionId}/split/preview`,
                    { day_start_time: dayStart.format("HH:mm") },
                    { withCredentials: true }
                );
                if (!cancelled) {
                    setRanges(response.data?.ranges ?? []);
                    setPreviewError(null);
                }
            } catch (error: any) {
                if (!cancelled) {
                    setRanges([]);
                    setPreviewError(error.response?.data?.error ?? "Could not preview the split.");
                }
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [open, mode, sessionId, dayStart?.format("HH:mm")]);

    const handleSplit = async () => {
        if (!sessionId) return;
        setSplitting(true);
        try {
            const response = await axios.post(
                `${API_URL}/instrumentsession/${sessionId}/split`,
                {
                    mode,
                    day_start_time: dayStart?.format("HH:mm"),
                    group_name: groupName || undefined,
                },
                { withCredentials: true }
            );
            message.success(response.data?.message ?? "Session split successfully.");
            onSplit(response.data?.session_ids ?? [], response.data?.session_group_id);
        } catch (error: any) {
            message.error(error.response?.data?.error ?? "Failed to split session.");
        } finally {
            setSplitting(false);
        }
    };

    // In day mode the preview tells us whether there is anything to split.
    const canSplit =
        mode === "day" ? ranges.length > 1 && !!dayStart : datedCollectionCount >= 2;

    return (
        <Modal
            open={open}
            title="Split into separate sessions"
            onCancel={onCancel}
            onOk={handleSplit}
            okText="Split"
            okButtonProps={{ disabled: !canSplit, loading: splitting }}
            width={640}
            destroyOnClose
        >
            <Form layout="vertical">
                <Form.Item label="Split by">
                    <Radio.Group value={mode} onChange={(e) => setMode(e.target.value)}>
                        <Radio.Button value="day">Calendar day</Radio.Button>
                        <Radio.Button value="collections" disabled={datedCollectionCount < 2}>
                            Collection
                        </Radio.Button>
                    </Radio.Group>
                </Form.Item>

                {mode === "day" ? (
                    <Form.Item
                        label="Each new day starts at"
                        help="Every occurrence of this time inside the session begins a new day. Days are contiguous — each one ends where the next begins — so no time is lost."
                    >
                        <TimePicker
                            value={dayStart}
                            onChange={setDayStart}
                            format="h:mm A"
                            use12Hours
                            minuteStep={15}
                            allowClear={false}
                        />
                    </Form.Item>
                ) : (
                    <Typography.Paragraph type="secondary">
                        Each of the {datedCollectionCount} dated collections moves onto its own new
                        session matching that collection's time range.
                    </Typography.Paragraph>
                )}

                <Form.Item
                    label="Group name"
                    help="The resulting sessions are linked together under this name so the block stays visible. Leave blank to name it after the original session."
                >
                    <Input
                        value={groupName}
                        onChange={(e) => setGroupName(e.target.value)}
                        placeholder="e.g. Krios March 2–4 booking"
                    />
                </Form.Item>

                {mode === "day" && previewError && (
                    <Alert type="warning" showIcon message={previewError} />
                )}

                {mode === "day" && !previewError && ranges.length > 0 && (
                    <>
                        <Typography.Text strong>
                            {ranges.length === 1
                                ? "This session stays as one — it does not cross the chosen time."
                                : `This will produce ${ranges.length} sessions:`}
                        </Typography.Text>
                        <Table
                            dataSource={ranges.map((range, index) => ({ ...range, key: index }))}
                            pagination={false}
                            size="small"
                            style={{ marginTop: 8 }}
                        >
                            <Table.Column
                                title="Day"
                                render={(_, __, index) => index + 1}
                                width={60}
                            />
                            <Table.Column
                                dataIndex="start_date"
                                title="Start"
                                render={(value: string) => dayjs(value).format("YYYY-MM-DD h:mm A")}
                            />
                            <Table.Column
                                dataIndex="end_date"
                                title="End"
                                render={(value: string) => dayjs(value).format("YYYY-MM-DD h:mm A")}
                            />
                            <Table.Column
                                title="Length"
                                render={(_, record: SplitRange) => {
                                    const hours = dayjs(record.end_date).diff(
                                        dayjs(record.start_date),
                                        "hour",
                                        true
                                    );
                                    return `${hours.toFixed(1)} h`;
                                }}
                            />
                        </Table>
                    </>
                )}
            </Form>
        </Modal>
    );
};
