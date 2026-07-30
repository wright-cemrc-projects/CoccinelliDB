import { Edit, useForm, useSelect } from "@refinedev/antd";
import { Form, Input, InputNumber, DatePicker, Select } from "antd";
import { InstrumentSession } from "@/src/type";
import dayjs from "dayjs";

export const CollectionEdit = () => {
    const { selectProps: sessionSelectProps } = useSelect({
        resource: "instrumentsession",
        optionLabel: (item: InstrumentSession) =>
            `Session #${item.id}${item.instrument?.name ? ` — ${item.instrument.name}` : ""}`,
        optionValue: "id",
    });

    const { formProps, saveButtonProps } = useForm();

    const handleFormSubmit = (values: any) => {
        const payload = {
            ...values,
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
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical" onFinish={handleFormSubmit}>
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
            </Form>
        </Edit>
    );
};
