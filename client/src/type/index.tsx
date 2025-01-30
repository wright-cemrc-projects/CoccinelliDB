export interface Facility {
    id: number;
    name: string;
}

export interface Person {
    primary_contact: boolean;
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    organization: string;
    address1: string;
    address2: string;
    state: string;
    country: string;
    telephone: string;
    net_id: number;
    start_date: Date;
    end_date: Date;
}

export interface Instrument {
    id: number;
    name: string;
    model: string;

}