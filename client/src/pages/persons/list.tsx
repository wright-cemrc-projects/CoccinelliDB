import {
    DeleteButton,
    EditButton, FilterDropdown,
    List,
    ShowButton,
    useTable,
} from "@refinedev/antd";
import {BaseRecord, getDefaultFilter} from "@refinedev/core";
import {Input, Space, Table} from "antd";
import {SearchOutlined} from "@ant-design/icons";

export const PersonList = () => {
    const { tableProps, filters } = useTable({
        syncWithLocation: true,
        filters: {
            initial: [
                {
                    field: "full_name",
                    operator: "contains",
                    value: undefined,
                },
            ],
        },
    });
    console.log(tableProps.dataSource);
    const transformedDataSource = tableProps.dataSource?.map((record) => ({
        ...record,
        full_name: `${record.first_name} ${record.last_name}`, 
        organization: !record.organization ? "None" : record.organization,
        start_date: !record.start_date ? "None" : record.start_date,
        address1: !record.address1 ? "None" : record.address1,
        address2: !record.address2 ? "None" : record.address2,
        country:  !record.country ? "None" : record.country,
        state: !record.state ? "None" : record.state,
        end_date: !record.end_date ? "None" : record.end_date,
        telephone: !record.telephone ? "None" : record.telephone,
    }));
    console.log(transformedDataSource)
    return (
        <List>
            <Table {...tableProps} dataSource={transformedDataSource} rowKey="id">
                <Table.Column dataIndex="id" title={"ID"} />
                <Table.Column
                    dataIndex="full_name"
                    title="Full Name"
                    defaultFilteredValue={getDefaultFilter("id", filters)}
                    filterIcon={<SearchOutlined />}
                    filterDropdown={(props) => (
                        <FilterDropdown {...props}>
                            <Input placeholder="Search Person" />
                        </FilterDropdown>
                    )}
                />
                <Table.Column dataIndex="net_id" title="Net ID"/>
                <Table.Column dataIndex="email" title="Email"/>
                <Table.Column dataIndex="start_date" title="Start Date"/>
                <Table.Column dataIndex="end_date" title="End Date"/>
                <Table.Column dataIndex="organization" title="Organization" />
                <Table.Column dataIndex="address1" title="Address1"/>
                <Table.Column dataIndex="address2" title="Address2"/>
                <Table.Column dataIndex="state" title="State"/>
                <Table.Column dataIndex="country" title="Country"/>
                <Table.Column dataIndex="telephone" title="Telephone"/>
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
