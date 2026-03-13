-- =============================================================================
-- JARVIS-Trader Supabase Schema
-- Run this in Supabase Dashboard → SQL Editor
-- =============================================================================

-- 1. Profiles (auto-created on signup via trigger)
create table public.profiles (
  id uuid references auth.users on delete cascade primary key,
  display_name text,
  tier text default 'free' check (tier in ('free', 'pro', 'enterprise')),
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamptz default now()
);

-- 2. Portfolio state
create table public.portfolios (
  user_id uuid references auth.users on delete cascade primary key,
  total_capital numeric default 100000,
  available_capital numeric default 100000,
  realized_pnl numeric default 0,
  peak_value numeric default 100000,
  positions jsonb default '[]',
  updated_at timestamptz default now()
);

-- 3. Trade history
create table public.trades (
  id text primary key,
  user_id uuid references auth.users on delete cascade not null,
  asset text not null,
  direction text not null check (direction in ('LONG', 'SHORT')),
  entry_price numeric not null,
  exit_price numeric not null,
  size numeric not null,
  capital_allocated numeric not null,
  opened_at timestamptz not null,
  closed_at timestamptz not null,
  pnl numeric not null,
  pnl_percent numeric not null
);

-- 4. User settings
create table public.user_settings (
  user_id uuid references auth.users on delete cascade primary key,
  settings jsonb default '{}',
  updated_at timestamptz default now()
);

-- Index for fast trade lookups
create index trades_user_id_idx on public.trades (user_id, closed_at desc);

-- =============================================================================
-- Row Level Security — users can only access their own data
-- =============================================================================

alter table public.profiles enable row level security;
alter table public.portfolios enable row level security;
alter table public.trades enable row level security;
alter table public.user_settings enable row level security;

-- Profiles
create policy "Users read own profile" on profiles for select using (auth.uid() = id);
create policy "Users update own profile" on profiles for update using (auth.uid() = id);

-- Portfolios
create policy "Users read own portfolio" on portfolios for select using (auth.uid() = user_id);
create policy "Users insert own portfolio" on portfolios for insert with check (auth.uid() = user_id);
create policy "Users update own portfolio" on portfolios for update using (auth.uid() = user_id);

-- Trades
create policy "Users read own trades" on trades for select using (auth.uid() = user_id);
create policy "Users insert own trades" on trades for insert with check (auth.uid() = user_id);

-- Settings
create policy "Users read own settings" on user_settings for select using (auth.uid() = user_id);
create policy "Users insert own settings" on user_settings for insert with check (auth.uid() = user_id);
create policy "Users update own settings" on user_settings for update using (auth.uid() = user_id);

-- =============================================================================
-- Auto-create profile + portfolio on signup
-- =============================================================================

create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)));

  insert into public.portfolios (user_id)
  values (new.id);

  insert into public.user_settings (user_id)
  values (new.id);

  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
