export type Booking = {
  booking_id: string;
  name: string;
  designation: string;
  department: string;
  lab: string;
  component: string;
  from_datetime: string;
  to_datetime: string;
  booked_at: string;
};

export type BookingFormValues = {
  name: string;
  designation: string;
  department: string;
  lab: string;
  component: string;
  from_datetime: string;
  to_datetime: string;
};

export type LaboratoryCatalog = Record<string, string[]>;

export type FlashMessage = {
  type: 'success' | 'error';
  text: string;
};
