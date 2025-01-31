import {Edit, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, DatePicker, Select} from "antd";
import dayjs from 'dayjs';
import {Facility, Instrument} from "@/src/type";

export const InstrumentSessionEdit = () => {
    const { formProps, saveButtonProps } = useForm({});
    const { selectProps: facilitySelectProps } = useSelect({
        resource: "facilities",
        optionLabel: (item: Facility) => `${item?.name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },

        ],
    });

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
    return (
        <Edit saveButtonProps={saveButtonProps} >
            <Form {...formProps} layout="vertical" >
                <Form.Item
                    label={"Start Date"}
                    name={["start_date"]}
                    rules={[
                        {
                            required: true, message: "Start Date is required"
                        },
                    ]}
                    getValueProps={(value) => ({ value: value ? dayjs(value) : "", })}
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
                    getValueProps={(value) => ({ value: value ? dayjs(value) : "", })}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }} // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"Facility ID"}
                    name={["facility_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...facilitySelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Project ID"}
                    name={["project_id"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>
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
            </Form>
        </Edit>
    );
};
