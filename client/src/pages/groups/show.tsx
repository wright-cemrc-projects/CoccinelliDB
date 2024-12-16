import { Show, TextField } from "@refinedev/antd";
import { useShow} from "@refinedev/core";
import { Divider, Typography } from "antd";
import { Person } from "@/src/type";
import { useParams } from "react-router-dom";
import { Text } from "@/src/components";
import { FilterDropdown, useTable } from "@refinedev/antd";

import {
  MailOutlined,
  PhoneOutlined,
  SearchOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Button, Card, Input, Select, Space, Table } from "antd";

const { Title } = Typography;

export const GroupShow = () => {
    const { queryResult } = useShow({});
    const { data, isLoading } = queryResult;
    const param = useParams();
    const { tableProps } = useTable<Person>({
        syncWithLocation: true,
        resource: `/groups/${param?.id}/persons`
    });
    
    const record = data?.data;

    return (
        <Show isLoading={isLoading}>
            <div style={{ marginBottom: "16px" }}>
                <Title level={5}>{"ID"}</Title>
                <TextField value={record?.id} />
            </div>

            <div style={{ marginBottom: "16px" }}>
                <Title level={5}>{"Name"}</Title>
                <TextField value={record?.name} />
            </div>


            <Card
                headStyle={{
                    borderBottom: "1px solid #D9D9D9",
                    marginBottom: "1px",
                    paddingLeft: "10px"
                }}
                title={
                    <>
                    <TeamOutlined />
                    <Text>Persons</Text>
                    </>
                }
                extra={
                    <>
                    <Text className="tertiary">Total persons: </Text>
                    <Text strong>
                        {tableProps?.pagination !== false && tableProps.pagination?.total}
                    </Text>
                    </>
                }
                bodyStyle={{padding: 0}}
            >
                <Table
                    {...tableProps}
                    rowKey="id"
                    pagination={{
                    ...tableProps.pagination,
                    showSizeChanger: false,
                    }}
                >
                    <Table.Column<Person>
                    title="Name"
                    dataIndex="name"
                    render={(_, record) => {
                        return (
                        <Space>
                            <Text
                            style={{
                                whiteSpace: "nowrap",
                            }}
                            >
                            {record.first_name} {record.last_name}
                            </Text>
                        </Space>
                        );
                    }}
                    />
                   
                   <Table.Column<Person>
                    title="Email"
                    dataIndex="email"
                    render={(_, record) => {
                        return (
                        <Space>
                            <Text
                            style={{
                                whiteSpace: "nowrap",
                            }}
                            >
                            {record.email} 
                            </Text>
                        </Space>
                        );
                    }}
                    />
                </Table>
            </Card>
        </Show>
    )

    
};