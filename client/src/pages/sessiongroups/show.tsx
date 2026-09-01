import { Show, TextField } from "@refinedev/antd";
import { useNavigation, useShow } from "@refinedev/core";
import { Table, Typography } from "antd";
import { InstrumentSession, SessionGroup } from "@/src/type";

import dayjs from "dayjs";

const { Title } = Typography;

/** A block of linked sessions, listed in order so a split booking reads day by day. */
export const SessionGroupShow = () => {
    const { query } = useShow<SessionGroup>({});
    const { data, isLoading } = query;
    const { edit, show } = useNavigation();

    const record = data?.data;
    const sessions = [...(record?.sessions ?? [])].sort(
        (a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
    );

    const totalHours = sessions.reduce((sum, session) => {
        if (!session.start_date || !session.end_date) return sum;
        return sum + dayjs(session.end_date).diff(dayjs(session.start_date), "hour", true);
    }, 0);

    return (
        <Show isLoading={isLoading}>
            <Title level={5}>{"Name"}</Title>
            <TextField value={record?.name ?? `Group ${record?.id}`} />
            <Title level={5}>{"Notes"}</Title>
            <TextField value={record?.notes || "—"} />
            <Title level={5}>{"Total Hours"}</Title>
            <TextField value={totalHours ? `${totalHours.toFixed(1)} h` : "—"} />

            <Title level={5} style={{ marginTop: 24 }}>
                {"Linked Sessions"}
            </Title>
            <Table dataSource={sessions} rowKey="id" pagination={false} size="small">
                <Table.Column dataIndex="id" title="ID" width={70} />
                <Table.Column
                    dataIndex={["instrument", "name"]}
                    title="Instrument"
                    render={(value: string | undefined) => value ?? "—"}
                />
                <Table.Column
                    dataIndex="start_date"
                    title="Start"
                    render={(value: string | null) =>
                        value ? dayjs(value).format("YYYY-MM-DD h:mm A") : "—"
                    }
                />
                <Table.Column
                    dataIndex="end_date"
                    title="End"
                    render={(value: string | null) =>
                        value ? dayjs(value).format("YYYY-MM-DD h:mm A") : "—"
                    }
                />
                <Table.Column
                    dataIndex="notes"
                    title="Notes"
                    render={(value: string | null) =>
                        value ? (
                            <Typography.Text
                                ellipsis={{ tooltip: value }}
                                style={{ maxWidth: 260, display: "inline-block" }}
                            >
                                {value}
                            </Typography.Text>
                        ) : (
                            "—"
                        )
                    }
                />
                <Table.Column
                    title="Actions"
                    render={(_, session: InstrumentSession) => (
                        <>
                            <Typography.Link onClick={() => show("instrumentsession", session.id)}>
                                View
                            </Typography.Link>
                            {" · "}
                            <Typography.Link onClick={() => edit("instrumentsession", session.id)}>
                                Edit
                            </Typography.Link>
                        </>
                    )}
                />
            </Table>
        </Show>
    );
};
