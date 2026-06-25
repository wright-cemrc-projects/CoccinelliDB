import { List, ShowButton, useTable } from "@refinedev/antd";
import { BaseRecord } from "@refinedev/core";
import { Space, Table, Tag } from "antd";
import { Collection } from "@/src/type";

export const CollectionList = () => {
    const { tableProps } = useTable<Collection>({
        syncWithLocation: true,
    });

    return (
        <List canCreate={false}>
            <Table {...tableProps} rowKey="id">
                <Table.Column dataIndex="id" title="ID" sorter />
                <Table.Column dataIndex="data_location" title="Data Location" />
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
                <Table.Column dataIndex="instrument_session_id" title="Session ID" />
                <Table.Column
                    title="Actions"
                    dataIndex="actions"
                    render={(_, record: BaseRecord) => (
                        <Space>
                            <ShowButton hideText size="small" recordItemId={record.id} />
                        </Space>
                    )}
                />
            </Table>
        </List>
    );
};
