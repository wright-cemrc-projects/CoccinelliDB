import { Edit, useForm } from "@refinedev/antd";
import { Form, Input, DatePicker } from "antd";
import dayjs from 'dayjs';
export const PersonEdit = () => {
    const { formProps, saveButtonProps } = useForm({});

    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
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

                        showTime // Enables time selection
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
                        showTime // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"First Name"}
                    name={["first_name"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Last Name"}
                    name={["last_name"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Email"}
                    name={["email"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>


                <Form.Item
                    label={"Net ID"}
                    name={["net_id"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Organization"}
                    name={["organization"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Address1"}
                    name={["address1"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Address2"}
                    name={["address2"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"State"}
                    name={["state"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Country"}
                    name={["country"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

                <Form.Item
                    label={"Telephone"}
                    name={["telephone"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>
            </Form>
        </Edit>
    );
};