import { List, useTable } from "@refinedev/antd";
import { Table } from "antd";
import dayjs from "dayjs";
import { RemoteSessionLog } from "@/src/type";

export const RemoteSessionLogList = () => {
    const { tableProps } = useTable<RemoteSessionLog>({
        syncWithLocation: true,
        sorters: {
            initial: [{ field: "start_date", order: "desc" }],
        },
    });

    return (
        <List canCreate={false}>
            <Table {...tableProps} rowKey="id">
                <Table.Column dataIndex="id" title="ID" />
                <Table.Column
                    dataIndex="start_date"
                    title="Start Date"
                    render={(value) => value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "—"}
                />
                <Table.Column
                    dataIndex="end_date"
                    title="End Date"
                    render={(value) => value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "—"}
                />
                <Table.Column
                    dataIndex="user"
                    title="User"
                    render={(user) => user ? `${user.first_name} ${user.last_name}` : "—"}
                />
                <Table.Column
                    dataIndex="instrument"
                    title="Instrument"
                    render={(instrument) => instrument?.name ?? "—"}
                />
                <Table.Column dataIndex="notes" title="Notes" />
            </Table>
        </List>
    );
};
