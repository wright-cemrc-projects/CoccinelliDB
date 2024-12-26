import {Edit, useForm, useSelect, useTable} from "@refinedev/antd";
import {Form, Input, Select, Tag} from "antd";
import {Person} from "@/src/type";
import {useEffect, useState} from "react";
import {useParams} from "react-router-dom";


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
    const param = useParams();
    const { tableProps } = useTable<Person>({
        syncWithLocation: true,
        resource: `/groups/${param?.id}/persons`
    });


    const initialPersons = queryResult?.data?.data?.persons ?? [];
    const initialName = queryResult?.data?.data?.name ?? [];
    const [primaryContact, setPrimaryContact] = useState<number | null>(
        initialPersons.find((person: any) => person.primary_contact)?.id ?? null
    );
    useEffect(() => {
        const primary = tableProps?.dataSource?.find((person: any) => person.primary_contact)?.id ?? null;
        setPrimaryContact(primary);
    }, [tableProps]);

    const handlePrimaryContactToggle = (personId: number) => {
        setPrimaryContact((prev) => (prev === personId ? null : personId));
    };

    const tagRender = (props: any) => {
        const { label, value, closable, onClose } = props;
        const isPrimary = primaryContact === value;
        return (
            <Tag
                color={isPrimary ? "gold" : "default"}
                closable={closable}
                onClose={onClose}
                style={{ display: "flex", alignItems: "center", cursor: "pointer" }}
                onClick={() => handlePrimaryContactToggle(value)}
            >
                {label} {isPrimary && "(Primary)"}
            </Tag>
        );
    };

    const handleFinish = (values: any) => {
        const formattedPersons = values.persons.map((personId: number) => ({
            id: personId,
            primary_contact: personId === primaryContact,
        }));
        const updatedValues = {
            ...values,
            persons: formattedPersons,
        };
        formProps.onFinish?.(updatedValues); // Pass the transformed data to the form's default handler
    };

    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical" initialValues={{persons: initialPersons, name: initialName}} onFinish={handleFinish} >
                <Form.Item
                    label={"Name"}
                    name={["name"]}
                >
                    <Input />
                </Form.Item>

                <Form.Item label={"Persons"} name="persons">
                    <Select
                        {...selectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}
                        mode="multiple"
                        tagRender={tagRender}
                    />
                </Form.Item>

            </Form>

        </Edit>
    );
};