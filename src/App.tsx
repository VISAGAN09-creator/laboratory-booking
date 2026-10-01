import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useCallback, useEffect, useMemo, useState } from 'react';
import rmkLogo from './assests/rmk.png';
import yearsLogo from './assests/31yrs.png';
import { DEPARTMENTS, DESIGNATIONS, LAB_CATALOG } from './data';
import { Booking, BookingFormValues, FlashMessage } from './types';
import { NAME_PATTERN, formatSlot, parseSlot, slotsOverlap } from './utils';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api';

const initialFormValues: BookingFormValues = {
  name: '',
  designation: '',
  department: '',
  lab: '',
  component: '',
  from_datetime: '',
  to_datetime: '',
};

function App() {
  const location = useLocation();

  return (
    <div className="page-frame">
      <header className="masthead">
        <div className="masthead__logos">
          <img
            className="crest crest--rmk"
            src={rmkLogo}
            alt="RMK Engineering College crest"
          />
          <div className="masthead__titles">
            <p className="eyebrow">Internal academic portal</p>
            <h1>RMK Engineering College</h1>
            <p className="subtitle">Center of Research &amp; Development</p>
            <p className="section-title">Research Facility Booking</p>
          </div>
          <img
            className="crest crest--years"
            src={yearsLogo}
            alt="31 years of academic excellence"
          />
        </div>
        {location.pathname !== '/' ? (
          <nav className="site-nav" aria-label="Primary">
            <Link to="/" className={location.pathname === '/' ? 'is-active' : ''}>
              Home
            </Link>
            <Link to="/book-now" className={location.pathname === '/book-now' ? 'is-active' : ''}>
              Book Now
            </Link>
            <Link to="/booked-details" className={location.pathname === '/booked-details' ? 'is-active' : ''}>
              Booked Details
            </Link>
          </nav>
        ) : null}
      </header>

      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/book-now" element={<BookingPage />} />
          <Route path="/booked-details" element={<BookedDetailsPage />} />
        </Routes>
      </main>

      <footer className="site-footer">
        <p>RMK Engineering College · RSM Nagar, Kavaraipettai, Tamil Nadu 601206</p>
        <p>Center of Research &amp; Development · Facility booking records are stored for internal coordination.</p>
      </footer>
    </div>
  );
}

function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="ornament" aria-hidden="true" />
        <p className="lede">
          Reserve laboratories, instruments, and computing resources for academic work, funded projects,
          and supervised research at the Center of Research &amp; Development.
        </p>
        <div className="cta-row">
          <Link className="cta-btn cta-btn--primary" to="/book-now">
            Book Now
          </Link>
          <Link className="cta-btn cta-btn--ghost" to="/booked-details">
            Booked Details
          </Link>
        </div>
      </section>

      <section className="info-grid" aria-label="College and facility information">
        <article className="info-card">
          <h2>About the Centre</h2>
          <p>
            CRD supports faculty and students with shared research infrastructure across computing,
            electronics, materials, energy, and prototyping labs.
          </p>
        </article>
        <article className="info-card">
          <h2>Booking window</h2>
          <p>
            Slots may be reserved in advance for up to 8 hours. Overlapping use of the same lab component
            is not permitted.
          </p>
        </article>
        <article className="info-card">
          <h2>Who can book</h2>
          <p>
            Students, faculty, research scholars, lab in-charges, heads of department, and approved
            external researchers may submit a request.
          </p>
        </article>
      </section>
    </>
  );
}

function BookingPage() {
  const navigate = useNavigate();
  const [values, setValues] = useState<BookingFormValues>(initialFormValues);
  const [flash, setFlash] = useState<FlashMessage[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const selectedLabComponents = useMemo(() => {
    if (!values.lab) return [];
    return LAB_CATALOG[values.lab as keyof typeof LAB_CATALOG] ?? [];
  }, [values.lab]);

  const handleFieldChange = (field: keyof BookingFormValues, value: string) => {
    setValues((previous) => {
      const updated = { ...previous, [field]: value };
      if (field === 'lab') {
        updated.component = '';
      }
      return updated;
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const errors: string[] = [];

    if (!NAME_PATTERN.test(values.name)) {
      errors.push('Enter a valid name using letters only.');
    }
    if (!DESIGNATIONS.includes(values.designation as (typeof DESIGNATIONS)[number])) {
      errors.push('Select a designation from the list.');
    }
    if (!DEPARTMENTS.includes(values.department as (typeof DEPARTMENTS)[number])) {
      errors.push('Select a department from the list.');
    }
    if (!(values.lab in LAB_CATALOG)) {
      errors.push('Select a research lab from the list.');
    } else if (!selectedLabComponents.includes(values.component)) {
      errors.push('Select a component that belongs to the chosen lab.');
    }

    const start = parseSlot(values.from_datetime);
    const end = parseSlot(values.to_datetime);

    if (!start || !end) {
      errors.push('Choose both a From and To date & time.');
    } else if (end <= start) {
      errors.push('The To time must be later than the From time.');
    } else if ((end.getTime() - start.getTime()) / (1000 * 60 * 60) > 8) {
      errors.push('A single booking cannot exceed 8 hours.');
    }

    if (errors.length > 0) {
      setFlash(errors.map((message) => ({ type: 'error', text: message })));
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });

      const data = await response.json();

      if (!response.ok) {
        setFlash((data.errors || ['Booking failed.']).map((msg: string) => ({ type: 'error', text: msg })));
        return;
      }

      setFlash([{ type: 'success', text: `Slot reserved. Booking ID ${data.booking_id}.` }]);
      setValues(initialFormValues);
      setTimeout(() => navigate('/booked-details'), 1500);
    } catch {
      setFlash([{ type: 'error', text: 'Could not reach the server. Make sure the backend is running.' }]);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="form-wrap">
      <header className="panel-head">
        <h2>Book Now</h2>
        <p>Fill the details below to reserve a research facility slot.</p>
      </header>

      {flash.length > 0 ? (
        <div className="flash-stack" role="status">
          {flash.map((item, index) => (
            <p key={`${item.type}-${index}`} className={`flash flash--${item.type}`}>
              {item.text}
            </p>
          ))}
        </div>
      ) : null}

      <form className="booking-form" onSubmit={handleSubmit} noValidate>
        <label className="field">
          <span>Name</span>
          <input
            type="text"
            name="name"
            maxLength={80}
            autoComplete="name"
            required
            placeholder="Enter full name"
            value={values.name}
            onChange={(event) => handleFieldChange('name', event.target.value)}
          />
        </label>

        <label className="field">
          <span>Designation</span>
          <select
            name="designation"
            required
            value={values.designation}
            onChange={(event) => handleFieldChange('designation', event.target.value)}
          >
            <option value="">Select designation</option>
            {DESIGNATIONS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Department</span>
          <select
            name="department"
            required
            value={values.department}
            onChange={(event) => handleFieldChange('department', event.target.value)}
          >
            <option value="">Select department</option>
            {DEPARTMENTS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Lab</span>
          <select
            name="lab"
            required
            value={values.lab}
            onChange={(event) => handleFieldChange('lab', event.target.value)}
          >
            <option value="">Select lab</option>
            {Object.keys(LAB_CATALOG).map((lab) => (
              <option key={lab} value={lab}>
                {lab}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Components</span>
          <select
            name="component"
            required
            value={values.component}
            onChange={(event) => handleFieldChange('component', event.target.value)}
          >
            <option value="">{values.lab ? 'Select a component' : 'Select a lab first'}</option>
            {selectedLabComponents.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="datetime-group">
          <legend>Date &amp; Time</legend>
          <label className="field">
            <span>From</span>
            <input
              type="datetime-local"
              name="from_datetime"
              required
              value={values.from_datetime}
              onChange={(event) => handleFieldChange('from_datetime', event.target.value)}
            />
          </label>
          <label className="field">
            <span>To</span>
            <input
              type="datetime-local"
              name="to_datetime"
              required
              value={values.to_datetime}
              onChange={(event) => handleFieldChange('to_datetime', event.target.value)}
            />
          </label>
        </fieldset>

        <button className="submit-btn" type="submit" disabled={submitting}>
          {submitting ? 'Submitting…' : 'Confirm booking'}
        </button>
      </form>
    </section>
  );
}

function BookedDetailsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');

  const fetchBookings = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/bookings`);
      if (response.ok) {
        setBookings(await response.json());
      }
    } catch {
      // silently fail — table will show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  const filteredBookings = bookings.filter((booking) => {
    const haystack = `${booking.booking_id} ${booking.name} ${booking.lab}`.toLowerCase();
    return haystack.includes(query.toLowerCase());
  });

  return (
    <section className="table-wrap">
      <header className="panel-head panel-head--row">
        <div>
          <h2>Booked Details</h2>
          <p>Reservations stored from the Book Now form.</p>
        </div>
        <label className="search-field">
          <span className="visually-hidden">Search bookings</span>
          <input
            type="search"
            placeholder="Search name, lab, or ID"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </header>

      {loading ? (
        <p style={{ textAlign: 'center', padding: '2rem' }}>Loading bookings…</p>
      ) : filteredBookings.length > 0 ? (
        <>
          <div className="table-scroll">
            <table className="records">
              <thead>
                <tr>
                  <th>Booking ID</th>
                  <th>Name</th>
                  <th>Designation</th>
                  <th>Department</th>
                  <th>Lab</th>
                  <th>Component</th>
                  <th>From</th>
                  <th>To</th>
                </tr>
              </thead>
              <tbody>
                {filteredBookings.map((row) => (
                  <tr key={row.booking_id}>
                    <td>{row.booking_id}</td>
                    <td>{row.name}</td>
                    <td>{row.designation}</td>
                    <td>{row.department}</td>
                    <td>{row.lab}</td>
                    <td>{row.component}</td>
                    <td>{formatSlot(row.from_datetime)}</td>
                    <td>{formatSlot(row.to_datetime)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="record-count">
            {filteredBookings.length} booking{filteredBookings.length !== 1 ? 's' : ''} on file.
          </p>
        </>
      ) : (
        <div className="empty-state">
          <p>
            No reservations yet. Use <Link to="/book-now">Book Now</Link> to add the first slot.
          </p>
        </div>
      )}
    </section>
  );
}

export default App;
