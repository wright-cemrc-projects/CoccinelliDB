import { DeleteButton, EditButton, List, ShowButton, useTable } from "@refinedev/antd";
import { BaseRecord, useGetIdentity, useNavigation } from "@refinedev/core";
import { Space, Table, Tag, Typography } from "antd";
import { Collection } from "@/src/type";

export const CollectionList = () => {
    const { tableProps } = useTable<Collection>({
        syncWithLocation: true,
        sorters: {
            initial: [{ field: "start_date", order: "asc" }],
        },
    });
    const { show } = useNavigation();
    // Deleting a collection is restricted to Admins on the backend; the button
    // is hidden for everyone else rather than shown-then-rejected. Every other
    // role sharing "collection" access (e.g. Editor) still gets full read/edit.
    const { data: identity } = useGetIdentity<{ roles?: string[] }>();
    const isAdmin = (identity?.roles ?? []).some((role) => role.toLowerCase() === "admin");

    return (
        <List canCreate={false}>
            <Table {...tableProps} rowKey="id">
                <Table.Column dataIndex="id" title="ID" sorter />
                <Table.Column dataIndex="data_location" title="Data Location" />
                <Table.Column
                    dataIndex="thumbnail_location"
                    title="Thumbnail Location"
                    render={(value: string | null) => value ?? "—"}
                />
                <Table.Column
                    dataIndex="collection_type"
                    title="Type"
                    render={(value: string | null) =>
                        value ? <Tag>{value}</Tag> : "—"
                    }
                />
                <Table.Column
                    dataIndex="start_date"
                    title="Start"
                    sorter
                    defaultSortOrder="ascend"
                    render={(value: string | null) =>
                        value ? new Date(value).toLocaleString() : "—"
                    }
                />
                <Table.Column
                    dataIndex="end_date"
                    title="End"
                    render={(value: string | null) =>
                        value ? new Date(value).toLocaleString() : "—"
                    }
                />
                <Table.Column dataIndex="total_image_count" title="Image Count" />
                <Table.Column
                    dataIndex="instrument_session_id"
                    title="Session ID"
                    render={(sessionId: number) => (
                        <Typography.Link onClick={() => show("instrumentsession", sessionId)}>
                            {sessionId}
                        </Typography.Link>
                    )}
                />
                <Table.Column
                    title="Actions"
                    dataIndex="actions"
                    render={(_, record: BaseRecord) => (
                        <Space>
                            <ShowButton hideText size="small" recordItemId={record.id} />
                            <EditButton hideText size="small" recordItemId={record.id} />
                            {isAdmin && (
                                <DeleteButton hideText size="small" recordItemId={record.id} />
                            )}
                        </Space>
                    )}
                />
            </Table>
        </List>
    );
};
