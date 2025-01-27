import {
    DeleteButton,
    EditButton, 
    List,
    ShowButton,
    useTable,
} from "@refinedev/antd";
import {BaseRecord} from "@refinedev/core";
import {Space, Table} from "antd";

export const InstrumentIssueList = () => {
    const { tableProps, filters } = useTable({
        syncWithLocation: true,
        filters: {
        },
    });
    console.log(tableProps.dataSource);
    const transformedDataSource = tableProps.dataSource?.map((record) => ({
        ...record,
    }));
    console.log(transformedDataSource)
    return (
        <List>
            <Table {...tableProps} dataSource={transformedDataSource} rowKey="id">
                <Table.Column dataIndex="id" title={"ID"} />
                <Table.Column dataIndex="instrument_id" title="Instrument_ID"/>
                <Table.Column dataIndex="start_date" title="Start Date"/>
                <Table.Column dataIndex="end_date" title="End Date"/>
                <Table.Column dataIndex="issue_title" title="Issue Title"/>
                <Table.Column dataIndex="issue_description" title="Issue Description"/>
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