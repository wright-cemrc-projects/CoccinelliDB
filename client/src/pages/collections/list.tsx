import { DeleteButton, EditButton, List, ShowButton, useTable } from "@refinedev/antd";
import { getDefaultFilter, HttpError, useGetIdentity, useNavigation } from "@refinedev/core";
import { Form, Input, Space, Table, Tag, Typography } from "antd";
import { Collection } from "@/src/type";

interface SearchFormValues {
    data_location?: string;
}

export const CollectionList = () => {
    const { tableProps, searchFormProps, filters } = useTable<Collection, HttpError, SearchFormValues>({
        syncWithLocation: true,
        sorters: {
            initial: [{ field: "start_date", order: "asc" }],
        },
        onSearch: (values) => [
            {
                field: "data_location",
                operator: "contains",
                value: values.data_location || undefined,
            },
        ],
    });
    const { show } = useNavigation();
    // Deleting a collection is restricted to Admins on the backend; the button
    // is hidden for everyone else rather than shown-then-rejected. Every other
    // role sharing "collection" access (e.g. Editor) still gets full read/edit.
    const { data: identity } = useGetIdentity<{ roles?: string[] }>();
    const isAdmin = (identity?.roles ?? []).some((role) => role.toLowerCase() === "admin");

    return (
        <List
            canCreate={false}
            headerButtons={({ defaultButtons }) => (
                <>
                    <Form
                        {...searchFormProps}
                        layout="inline"
                        initialValues={{
                            data_location: getDefaultFilter("data_location", filters, "contains"),
                        }}
                    >
                        <Form.Item name="data_location" noStyle>
                            <Input.Search
                                placeholder="Search by path (partial or full)"
                                allowClear
                                style={{ width: 320 }}
                                onSearch={() => searchFormProps.form?.submit()}
                            />
                        </Form.Item>
                    </Form>
                    {defaultButtons}
                </>
            )}
        >
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
                <Table.Column dataIndex="lamella_count" title="Lamella Count" render={(value: number | null) => value ?? "—"} />
                <Table.Column
                    dataIndex="editable"
                    title="Status"
                    render={(value: boolean) => (
                        <Tag color={value ? "green" : "gold"}>{value ? "Editable" : "Finalized"}</Tag>
                    )}
                />
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
                    render={(_, record: Collection) => (
                        <Space>
                            <ShowButton hideText size="small" recordItemId={record.id} />
                            <EditButton hideText size="small" recordItemId={record.id} />
                            {isAdmin && (
                                <DeleteButton
                                    hideText
                                    size="small"
                                    recordItemId={record.id}
                                    disabled={!record.editable}
                                    title={
                                        !record.editable
                                            ? "Finalized collections must be unlocked before they can be deleted."
                                            : undefined
                                    }
                                />
                            )}
                        </Space>
                    )}
                />
            </Table>
        </List>
    );
};
