import {Edit, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, Select} from "antd";
import {Facility} from "@/src/type";
export const ProjectEdit = () => {
    const { formProps, saveButtonProps } = useForm({});
    const { selectProps } = useSelect({
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
    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
                <Form.Item
                    label={"Project_ID"}
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
                    label={"Facility_ID"}
                    name={["facility_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...selectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
            </Form>
        </Edit>
    );
};