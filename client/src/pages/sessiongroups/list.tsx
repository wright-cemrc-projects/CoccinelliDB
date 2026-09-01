import { DeleteButton, EditButton, List, ShowButton, useTable } from "@refinedev/antd";
import { Space, Table, Typography } from "antd";
import { InstrumentSession, SessionGroup } from "@/src/type";

/** Time range covered by every session in a block, so a group reads like the booking it came from. */
const groupRange = (sessions: InstrumentSession[]) => {
    const dates = sessions
        .flatMap((session) => [session.start_date, session.end_date])
        .filter(Boolean)
        .map((value) => new Date(value as unknown as string).getTime());
    if (dates.length === 0) {
        return "—";
    }
    const start = new Date(Math.min(...dates));
    const end = new Date(Math.max(...dates));
    return `${start.toLocaleDateString()} – ${end.toLocaleDateString()}`;
};

export const SessionGroupList = () => {
    const { tableProps } = useTable<SessionGroup>({
        syncWithLocation: true,
    });

    return (
        <List>
            <Table {...tableProps} rowKey="id">
                <Table.Column dataIndex="id" title="ID" width={70} sorter />
                <Table.Column
                    dataIndex="name"
                    title="Name"
                    render={(value: string | null, record: SessionGroup) =>
                        value ?? `Group ${record.id}`
                    }
                />
                <Table.Column
                    title="Sessions"
                    width={100}
                    render={(_, record: SessionGroup) => record.sessions?.length ?? 0}
                />
                <Table.Column
                    title="Covers"
                    render={(_, record: SessionGroup) => groupRange(record.sessions ?? [])}
                />
                <Table.Column
                    dataIndex="notes"
                    title="Notes"
                    render={(value: string | null) =>
                        value ? (
                            <Typography.Text
                                ellipsis={{ tooltip: value }}
                                style={{ maxWidth: 320, display: "inline-block" }}
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
                    dataIndex="actions"
                    render={(_, record: SessionGroup) => (
                        <Space>
                            <ShowButton hideText size="small" recordItemId={record.id} />
                            <EditButton hideText size="small" recordItemId={record.id} />
                            <DeleteButton hideText size="small" recordItemId={record.id} />
                        </Space>
                    )}
                />
            </Table>
        </List>
    );
};
