import {Create, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, DatePicker, Select} from "antd";
import {Instrument} from "@/src/type";

import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone"

dayjs.extend(utc);
dayjs.extend(timezone);

export const InstrumentIssueCreate = () => {
    const { formProps, saveButtonProps } = useForm({});
    const { selectProps: instrumentSelectProps } = useSelect({
        resource: "instruments",
        optionLabel: (item: Instrument) => `${item?.name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },

        ],
    });

    const handleFormSubmit = (values: any) => {
        const payload = { ...values,
            start_date: values.start_date
                ? dayjs(values.start_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
            end_date: values.end_date
                ? dayjs(values.end_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
        }
        formProps.onFinish?.(payload);
    };

    return (
        <Create saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical" onFinish={handleFormSubmit}>
                <Form.Item
                    label={"Instrument ID"}
                    name={["instrument_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...instrumentSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Instrument Offline"}
                    name={["instrument_offline"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Boolean />
                </Form.Item>
                <Form.Item
                    label={"Issue Title"}
                    name={["issue_title"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>
                <Form.Item
                    label={"Issue Description"}
                    name={["issue_description"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input.TextArea />
                </Form.Item>
                <Form.Item
                    label={"Start Date"}
                    name={["start_date"]}
                    rules={[
                        {
                            required: true, message: "Start Date is required"
                        },
                    ]}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }} // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"End Date"}
                    name={["end_date"]}
                    rules={[
                        {
                            required: true, message: "End Date is required"
                        },
                    ]}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }} // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
            </Form>
        </Create>
    );
};