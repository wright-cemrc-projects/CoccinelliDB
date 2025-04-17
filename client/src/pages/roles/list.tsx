import {
    DeleteButton,
    EditButton,
    List,
    ShowButton,
    useTable,
} from "@refinedev/antd";
import {BaseRecord} from "@refinedev/core";
import {Space, Table} from "antd";

export const RoleList = () => {
    const { tableProps, filters } = useTable({
        syncWithLocation: true,
        filters: {
        },
    });
    const transformedDataSource = tableProps.dataSource?.map((record) => ({
        ...record,
        name: record.name,
    }));
    return (
        <List>
            <Table {...tableProps} dataSource={transformedDataSource} rowKey="id">
                <Table.Column dataIndex="name" title="Name"/>
                <Table.Column
                    title={"Actions"}
                    dataIndex="actions"
                    render={(_, record: BaseRecord) => (
                        <Space>
                            <EditButton hideText size="small" recordItemId={record.id} />
                            <ShowButton hideText size="small" recordItemId={record.id} />
                            <DeleteButton hideText size="small" recordItemId={record.id} />
                        </Space>
                    )}
                />
            </Table>
        </List>
    );
};
