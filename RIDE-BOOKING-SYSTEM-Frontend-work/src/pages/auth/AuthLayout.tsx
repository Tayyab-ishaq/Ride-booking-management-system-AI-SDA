import { ReactNode } from 'react';

export function AuthLayout({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#0A0C10] text-white">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 left-[-8rem] h-96 w-96 rounded-full bg-[#F5A623]/20 blur-3xl" />
        <div className="absolute right-[-6rem] top-24 h-80 w-80 rounded-full bg-[#3B82F6]/20 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-[#8B5CF6]/15 blur-3xl" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col lg:flex-row">
        <div className="flex flex-1 items-center px-6 py-16 lg:px-12">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.3em] text-[#94A3B8]">
              {eyebrow}
            </div>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              {title}
            </h1>
            <p className="mt-4 max-w-lg text-base leading-7 text-[#94A3B8]">
              {description}
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                ['Secure login', 'Email, phone, and OTP flows in one place.'],
                ['Role ready', 'Rider, driver, and admin journeys prepared.'],
                ['API friendly', 'Swap in your backend routes where marked.'],
              ].map(([label, copy]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
                  <div className="text-sm font-medium text-white">{label}</div>
                  <div className="mt-2 text-sm leading-6 text-[#94A3B8]">{copy}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 pb-16 lg:px-12 lg:py-16">
          <div className="w-full max-w-md rounded-[2rem] border border-white/10 bg-[#12151C]/95 p-6 shadow-2xl shadow-black/40 backdrop-blur-xl sm:p-8">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}