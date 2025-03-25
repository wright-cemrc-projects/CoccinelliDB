import {Create, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, DatePicker, Select} from "antd";
import {Facility, Instrument, Person, Project} from "@/src/type";

export const InstrumentSessionCreate = () => {
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
    const { selectProps: personSelectProps } = useSelect({
        resource: "persons",
        optionLabel: (item: Person) => `${item?.first_name} ${item?.last_name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "first_name",
                operator: "contains",
                value: value,
            },
            {
                field: "last_name",
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
    const { selectProps: projectSelectProps } = useSelect({
        resource: "projects",
        optionLabel: (item: Project) => `${item?.project_id}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "project_id",
                operator: "contains",
                value: value,
            },

        ],
    });
    return (
        <Create saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
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
                        showTime={{ use12Hours: true, format: "HH:mm a" }}  // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"Facility"}
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
                    label={"Project"}
                    name={["project_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...projectSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Instrument"}
                    name={["instrument_id"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Select
                        {...instrumentSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item label={"Persons"} name="persons">
                    <Select
                        {...personSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}
                        mode="multiple"

                    />
                </Form.Item>
            </Form>
        </Create>
    );
};
