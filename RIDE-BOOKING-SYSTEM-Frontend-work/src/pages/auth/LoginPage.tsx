import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from './AuthLayout';
import { ROUTES } from '../../routes/routeConfig';
import { useAuthContext } from '../../context/AuthContext';

type LoginFieldErrors = {
  identifier?: string;
  password?: string;
  general?: string;
};

function parseLoginErrors(caughtError: unknown): LoginFieldErrors {
  const resp = (caughtError as any)?.response;
  const fallback: LoginFieldErrors = {
    general: 'Login failed. Please check your credentials.',
  };

  if (!resp?.data) {
    return fallback;
  }

  const detail = resp.data.detail;
  if (Array.isArray(detail)) {
    const errors: LoginFieldErrors = {};

    for (const item of detail) {
      const message = item?.msg ?? (typeof item === 'string' ? item : undefined);
      const location = Array.isArray(item?.loc) ? item.loc : [];
      const field = location[location.length - 1];

      if (!message) {
        continue;
      }

      if (field === 'email' || field === 'phone') {
        errors.identifier = message;
      } else if (field === 'password') {
        errors.password = message;
      } else {
        errors.general = errors.general ?? message;
      }
    }

    return Object.keys(errors).length > 0 ? errors : fallback;
  }

  if (typeof detail === 'string') {
    return { password: detail, general: detail };
  }

  if (typeof resp.data === 'string') {
    return { general: resp.data };
  }

  return fallback;
}

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuthContext();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<LoginFieldErrors>({});
  const [touched, setTouched] = useState({
    identifier: false,
    password: false,
  });
  const inputClassName = (hasError: boolean) =>
    `w-full rounded-2xl border bg-[#0F131A] px-4 py-3 text-white outline-none transition placeholder:text-[#64748B] ${
      hasError ? 'border-red-500 focus:border-red-400' : 'border-white/10 focus:border-[#F5A623]'
    }`;

  const showFieldError = (field: keyof typeof touched, value: string, message?: string) =>
    touched[field] && (!value.trim() || Boolean(message));

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const payload = identifier.includes('@')
        ? { email: identifier, password }
        : { phone: identifier, password };

      await login(payload);
      navigate(ROUTES.APP_HOME, { replace: true });
    } catch (caughtError: unknown) {
      setErrors(parseLoginErrors(caughtError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      eyebrow="Ride Booking System"
      title="Welcome back"
      description="Sign in to access your rider, driver, or admin dashboard and continue your booking workflow."
    >
      <div>
        <div className="text-sm uppercase tracking-[0.24em] text-[#94A3B8]">Sign in</div>
        <h2 className="mt-2 text-2xl font-semibold text-white">Continue to your account</h2>
      </div>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
        <div>
          <label className="mb-2 block text-sm font-medium text-[#CBD5E1]">Email or phone</label>
          <input
            type="text"
            value={identifier}
            onChange={(event) => {
              setIdentifier(event.target.value);
              if (errors.identifier && event.target.value.trim()) {
                setErrors((current) => ({ ...current, identifier: undefined }));
              }
            }}
            onBlur={() => {
              setTouched((current) => ({ ...current, identifier: true }));
              if (!identifier.trim()) {
                setErrors((current) => ({ ...current, identifier: 'Email or phone is required.' }));
              }
            }}
            placeholder="name@example.com or +123456789"
            aria-invalid={showFieldError('identifier', identifier, errors.identifier)}
            className={inputClassName(Boolean(errors.identifier))}
            required
          />
          {showFieldError('identifier', identifier, errors.identifier) ? (
            <p className="mt-2 text-sm text-red-300">{errors.identifier ?? 'Email or phone is required.'}</p>
          ) : null}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-[#CBD5E1]">Password</label>
          <input
            type="password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              if (errors.password && event.target.value.trim()) {
                setErrors((current) => ({ ...current, password: undefined }));
              }
            }}
            onBlur={() => {
              setTouched((current) => ({ ...current, password: true }));
              if (!password) {
                setErrors((current) => ({ ...current, password: 'Password is required.' }));
              }
            }}
            placeholder="Enter your password"
            aria-invalid={showFieldError('password', password, errors.password)}
            className={inputClassName(Boolean(errors.password))}
            required
          />
          {showFieldError('password', password, errors.password) ? (
            <p className="mt-2 text-sm text-red-300">{errors.password ?? 'Password is required.'}</p>
          ) : null}
        </div>

        {errors.general ? (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            <div>{errors.general}</div>
          </div>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center rounded-2xl bg-[#F5A623] px-4 py-3 font-medium text-[#0A0C10] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link to={ROUTES.REGISTER} className="text-sm text-[#94A3B8] transition hover:text-white">
          Don't have an account? Create one
        </Link>
      </div>
    </AuthLayout>
  );
}