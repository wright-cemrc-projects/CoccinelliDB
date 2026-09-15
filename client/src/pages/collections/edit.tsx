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

    // Two separate things, deliberately not one shared boolean:
    //   - `locked`: was this record ALREADY finalized when it loaded, and not
    //     yet unlocked? Drives whether the form/Save button are interactive at
    //     all. Only changes via handleUnlock's immediate call (unlocking a
    //     finalized collection has to be its own request — the backend refuses
    //     to bundle it with other field changes, see update_collection — and
    //     only an Admin may do it).
    //   - `editable`: what the "Editable" switch is currently set to, for the
    //     *next* save. Freely toggleable in either direction whenever the form
    //     isn't locked; this is what finalizes the record when you hit Save.
    // Conflating these into one variable was the bug: gating Save on the
    // switch's own current value meant flipping it off to finalize disabled
    // Save before you could ever click it.
    const [locked, setLocked] = useState(false);
    const [editable, setEditable] = useState(true);
    const [unlocking, setUnlocking] = useState(false);

    useEffect(() => {
        if (record) {
            setEditable(record.editable);
            setLocked(!record.editable);
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
            setLocked(false);
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
        <Edit saveButtonProps={{ ...saveButtonProps, disabled: locked }}>
            {locked && (
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
            <Form {...formProps} layout="vertical" onFinish={handleFormSubmit} disabled={locked}>
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
                {!locked && (
                    <Form.Item
                        label="Editable"
                        tooltip="Turn off to finalize this collection and protect it from further changes (including from the instrument API) once you save. Anyone with edit access can finalize; only an Admin can unlock it again."
                    >
                        <Space>
                            <Switch
                                checked={editable}
                                checkedChildren="Editable"
                                unCheckedChildren="Finalized"
                                onChange={(checked) => setEditable(checked)}
                            />
                            <Typography.Text type="secondary">
                                {editable
                                    ? "Turn off and save to finalize this collection."
                                    : "Will be finalized when you save."}
                            </Typography.Text>
                        </Space>
                    </Form.Item>
                )}
            </Form>
        </Edit>
    );
};
