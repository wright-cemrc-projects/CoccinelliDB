import {
    DeleteButton,
    EditButton, 
    List,
    ShowButton,
    useTable,
} from "@refinedev/antd";
import {BaseRecord} from "@refinedev/core";
import {Space, Table} from "antd";

export const ProjectList = () => {
    const { tableProps, filters } = useTable({
        syncWithLocation: true,
        filters: {
        },
    });
    const transformedDataSource = tableProps.dataSource?.map((record) => ({
        ...record,
    }));
    return (
        <List>
            <Table {...tableProps} dataSource={transformedDataSource} rowKey="id">
                <Table.Column dataIndex="id" title={"ID"} />
                <Table.Column dataIndex="project_id" title="Project_ID"/>
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