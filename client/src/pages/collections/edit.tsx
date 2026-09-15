import { useEffect, useState } from "react";
import { Edit, useForm, useSelect } from "@refinedev/antd";
import { useGetIdentity } from "@refinedev/core";
import { Alert, App, Button, Form, Input, InputNumber, DatePicker, Select, Space, Switch, Typography } from "antd";
import { Collection, InstrumentSession } from "@/src/type";
import axios from "axios";
import dayjs from "dayjs";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

export const CollectionEdit = () => {
    const { selectProps: sessionSelectProps } = useSelect({
        resource: "instrumentsession",
        optionLabel: (item: InstrumentSession) =>
            `Session #${item.id}${item.instrument?.name ? ` — ${item.instrument.name}` : ""}`,
        optionValue: "id",
    });

    const { message } = App.useApp();
    const { data: identity } = useGetIdentity<{ roles?: string[] }>();
    const isAdmin = (identity?.roles ?? []).some((role) => role.toLowerCase() === "admin");

    const { formProps, saveButtonProps, queryResult } = useForm<Collection>();
    const record = queryResult?.data?.data;

    // The record's "editable" flag isn't a plain form field: unlocking a
    // finalized collection has to happen as its own request (the backend
    // refuses to bundle it with other field changes — see update_collection),
    // and only an Admin may do it. Tracked separately so it can drive the
    // rest of the form's disabled state and trigger that immediate call.
    const [editable, setEditable] = useState(true);
    const [unlocking, setUnlocking] = useState(false);

    useEffect(() => {
        if (record) {
            setEditable(record.editable);
        }
    }, [record]);

    const handleUnlock = async () => {
        if (!record) return;
        setUnlocking(true);
        try {
            await axios.patch(
                `${API_URL}/collection/${record.id}`,
                { editable: true },
                { withCredentials: true }
            );
            setEditable(true);
            message.success("Collection unlocked. You can now edit it.");
        } catch (error: any) {
            message.error(error.response?.data?.error ?? "Failed to unlock collection.");
        } finally {
            setUnlocking(false);
        }
    };

    const handleFormSubmit = (values: any) => {
        const payload = {
            ...values,
            editable,
            start_date: values.start_date
                ? dayjs(values.start_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
            end_date: values.end_date
                ? dayjs(values.end_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
        };
        formProps.onFinish?.(payload);
    };

    return (
        <Edit saveButtonProps={{ ...saveButtonProps, disabled: !editable }}>
            {!editable && (
                <Alert
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="This collection is finalized"
                    description={
                        isAdmin
                            ? "Its values are protected from changes, including from the instrument API. Unlock it to make a correction."
                            : "Its values are protected from changes, including from the instrument API. Only an Admin can unlock it."
                    }
                    action={
                        isAdmin && (
                            <Button loading={unlocking} onClick={handleUnlock}>
                                Unlock
                            </Button>
                        )
                    }
                />
            )}
            <Form {...formProps} layout="vertical" onFinish={handleFormSubmit} disabled={!editable}>
                <Form.Item
                    label="Instrument Session"
                    name={["instrument_session_id"]}
                    rules={[{ required: true, message: "Instrument Session is required" }]}
                >
                    <Select {...sessionSelectProps} style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item label="Type" name={["collection_type"]}>
                    <Select
                        allowClear
                        style={{ width: "100%" }}
                        options={[
                            { label: "Screening", value: "Screening" },
                            { label: "SPA", value: "SPA" },
                            { label: "CryoET", value: "CryoET" },
                        ]}
                    />
                </Form.Item>
                <Form.Item label="Data Location" name={["data_location"]}>
                    <Input />
                </Form.Item>
                <Form.Item
                    label="Thumbnail Location"
                    name={["thumbnail_location"]}
                    tooltip="Optional. Folder scanned for tilt-series thumbnails. Defaults to Data Location when left blank."
                >
                    <Input />
                </Form.Item>
                <Form.Item
                    label="Start"
                    name={["start_date"]}
                    getValueProps={(value) => ({ value: value ? dayjs(value) : "" })}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }}
                        format="YYYY-MM-DD HH:mm:ss"
                    />
                </Form.Item>
                <Form.Item
                    label="End"
                    name={["end_date"]}
                    getValueProps={(value) => ({ value: value ? dayjs(value) : "" })}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }}
                        format="YYYY-MM-DD HH:mm:ss"
                    />
                </Form.Item>
                <Form.Item label="Image Count" name={["total_image_count"]}>
                    <InputNumber min={0} style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item label="Lamella Count" name={["lamella_count"]}>
                    <InputNumber min={0} style={{ width: "100%" }} />
                </Form.Item>
                {editable && (
                    <Form.Item
                        label="Editable"
                        tooltip="Turn off to finalize this collection and protect it from further changes (including from the instrument API). Anyone with edit access can finalize; only an Admin can unlock it again."
                    >
                        <Space>
                            <Switch
                                checked={editable}
                                checkedChildren="Editable"
                                unCheckedChildren="Finalized"
                                onChange={(checked) => setEditable(checked)}
                            />
                            <Typography.Text type="secondary">
                                {editable ? "Save to finalize instead." : "Will be finalized on save."}
                            </Typography.Text>
                        </Space>
                    </Form.Item>
                )}
            </Form>
        </Edit>
    );
};
