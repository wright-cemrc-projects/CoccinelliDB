import {Edit, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, Select} from "antd";
import {Person} from "@/src/type";


export const GroupEdit = () => {
    const { formProps, saveButtonProps, queryResult } = useForm({
        meta: {
            populate: ["persons"],
        },
    });
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
    const initialPersons = queryResult?.data?.data?.persons ?? [];
    const initialName = queryResult?.data?.data?.name ?? [];
    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical" initialValues={{persons: initialPersons, name: initialName}}>
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

                <Form.Item name="persons">
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