import {Edit, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, Select} from "antd";
import {Person} from "@/src/type";


export const GroupEdit = () => {
    const { formProps, saveButtonProps } = useForm({});
    const { selectProps } = useSelect({
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
    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
                <Form.Item
                    label={"Name"}
                    name={["name"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item noStyle name="userIds">
                    <Select
                        {...selectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}
                        mode="multiple"
                    />
                </Form.Item>

            </Form>

        </Edit>
    );
};