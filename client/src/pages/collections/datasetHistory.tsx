import { useEffect, useState } from "react";
import { useSelect } from "@refinedev/antd";
import { useGetIdentity } from "@refinedev/core";
import { App, AutoComplete, Button, DatePicker, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, Typography } from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import axios from "axios";
import dayjs from "dayjs";
import { DatasetHistory, Person } from "@/src/type";

const { Title } = Typography;
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

const ACTION_OPTIONS = [
    { value: "Removed" },
    { value: "Moved" },
    { value: "Archived" },
];

interface DatasetHistoryPanelProps {
    collectionId: number;
}

export const DatasetHistoryPanel = ({ collectionId }: DatasetHistoryPanelProps) => {
    const { message } = App.useApp();
    const { data: identity } = useGetIdentity<{ roles?: string[] }>();
    const isAdmin = (identity?.roles ?? []).some((role) => role.toLowerCase() === "admin");

    const [records, setRecords] = useState<DatasetHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [editing, setEditing] = useState<DatasetHistory | null>(null);
    const [saving, setSaving] = useState(false);
    const [form] = Form.useForm();

    const { selectProps: personSelectProps } = useSelect<Person>({
        resource: "persons",
        optionLabel: (item: Person) => `${item.first_name} ${item.last_name}`,
        optionValue: "id",
        onSearch: (value) => [
            { field: "first_name", operator: "contains", value },
        ],
    });

    const fetchHistory = () => {
        setLoading(true);
        axios
            .get(`${API_URL}/collection/${collectionId}/history`, { withCredentials: true })
            .then((response) => setRecords(response.data ?? []))
            .catch((err) => console.error("Failed to fetch dataset history", err))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        if (collectionId) fetchHistory();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [collectionId]);

    const openCreate = () => {
        setEditing(null);
        form.resetFields();
        setModalOpen(true);
    };

    const openEdit = (record: DatasetHistory) => {
        setEditing(record);
        form.setFieldsValue({
            ...record,
            completed_by_id: record.completed_by_id,
            date: record.date ? dayjs(record.date) : null,
            approval_date: record.approval_date ? dayjs(record.approval_date) : null,
        });
        setModalOpen(true);
    };

    const handleDelete = (id: number) => {
        axios
            .delete(`${API_URL}/datasethistory/${id}`, { withCredentials: true })
            .then(() => {
                message.success("Dataset history record deleted.");
                fetchHistory();
            })
            .catch((err) => message.error(err.response?.data?.error ?? "Failed to delete record."));
    };

    const handleSubmit = async () => {
        const values = await form.validateFields();
        const payload = {
            ...values,
            date: values.date ? dayjs(values.date).format("YYYY-MM-DDTHH:mm:ss[Z]") : null,
            approval_date: values.approval_date ? dayjs(values.approval_date).format("YYYY-MM-DDTHH:mm:ss[Z]") : null,
        };

        setSaving(true);
        const request = editing
            ? axios.patch(`${API_URL}/datasethistory/${editing.id}`, payload, { withCredentials: true })
            : axios.post(`${API_URL}/collection/${collectionId}/history`, payload, { withCredentials: true });

        request
            .then(() => {
                message.success(editing ? "Dataset history record updated." : "Dataset history record created.");
                setModalOpen(false);
                fetchHistory();
            })
            .catch((err) => message.error(err.response?.data?.error ?? "Failed to save record."))
            .finally(() => setSaving(false));
    };

    const columns = [
        {
            title: "Date",
            dataIndex: "date",
            render: (value: string | null) => (value ? new Date(value).toLocaleString() : "—"),
        },
        { title: "Action", dataIndex: "action", render: (value: string | null) => value ?? "—" },
        { title: "Location", dataIndex: "location", render: (value: string | null) => value ?? "—" },
        { title: "Backup Location", dataIndex: "backup_location", render: (value: string | null) => value ?? "—" },
        { title: "Backup Path", dataIndex: "backup_path", render: (value: string | null) => value ?? "—" },
        {
            title: "Size (TB)",
            dataIndex: "dataset_size_tb",
            render: (value: number | null) => (value ?? "—"),
        },
        {
            title: "Completed By",
            dataIndex: "completed_by",
            render: (value: DatasetHistory["completed_by"]) =>
                value ? `${value.first_name} ${value.last_name}` : "—",
        },
        {
            title: "Retention (months)",
            dataIndex: "retention_period_months",
            render: (value: number | null) => (value ?? "—"),
        },
        {
            title: "Approval Date",
            dataIndex: "approval_date",
            render: (value: string | null) => (value ? new Date(value).toLocaleDateString() : "—"),
        },
        { title: "Notes", dataIndex: "notes", render: (value: string | null) => value ?? "—" },
        {
            title: "",
            key: "actions",
            render: (_: unknown, record: DatasetHistory) => (
                <Space>
                    <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
                    {isAdmin && (
                        <Popconfirm title="Delete this record?" onConfirm={() => handleDelete(record.id)}>
                            <Button size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <>
            <Title level={5} style={{ marginTop: 24 }}>
                <Space>
                    {"Dataset History"}
                    <Button size="small" icon={<PlusOutlined />} onClick={openCreate}>
                        Add Record
                    </Button>
                </Space>
            </Title>
            <Table
                rowKey="id"
                size="small"
                loading={loading}
                dataSource={records}
                columns={columns}
                pagination={false}
                locale={{ emptyText: "No history recorded for this collection." }}
            />

            <Modal
                title={editing ? "Edit Dataset History Record" : "Add Dataset History Record"}
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                onOk={handleSubmit}
                confirmLoading={saving}
                destroyOnClose
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        label="Completed By"
                        name="completed_by_id"
                        rules={[{ required: true, message: "Completed By is required" }]}
                    >
                        <Select {...personSelectProps} />
                    </Form.Item>
                    <Form.Item
                        label="Action"
                        name="action"
                        rules={[{ required: true, message: "Action is required" }]}
                    >
                        <AutoComplete options={ACTION_OPTIONS} filterOption />
                    </Form.Item>
                    <Form.Item label="Location" name="location" tooltip="Where the data was moved to, if applicable">
                        <Input.TextArea rows={2} />
                    </Form.Item>
                    <Form.Item label="Backup Location" name="backup_location" tooltip="Storage system/device the backup lives on">
                        <Input.TextArea rows={2} />
                    </Form.Item>
                    <Form.Item label="Backup Path" name="backup_path" tooltip="Full path to the backup copy">
                        <Input.TextArea rows={2} />
                    </Form.Item>
                    <Form.Item label="Dataset Size (TB)" name="dataset_size_tb">
                        <InputNumber min={0} step={0.1} style={{ width: "100%" }} />
                    </Form.Item>
                    <Form.Item label="Date" name="date" rules={[{ required: true, message: "Date is required" }]}>
                        <DatePicker showTime style={{ width: "100%" }} />
                    </Form.Item>
                    <Form.Item label="Retention Period (months)" name="retention_period_months">
                        <InputNumber min={0} style={{ width: "100%" }} />
                    </Form.Item>
                    <Form.Item label="Approval Date" name="approval_date">
                        <DatePicker style={{ width: "100%" }} />
                    </Form.Item>
                    <Form.Item label="Notes" name="notes">
                        <Input.TextArea rows={3} />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    );
};
