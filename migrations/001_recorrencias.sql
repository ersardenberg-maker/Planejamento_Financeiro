create table if not exists recorrencias (
  id uuid primary key default gen_random_uuid(),
  categoria_id uuid not null references categorias(id),
  descricao varchar(255) not null,
  valor numeric(12, 2) not null,
  dia smallint not null check (dia between 1 and 31),
  meio_pagamento varchar(30) not null default 'outros',
  cartao_id uuid references cartoes(id),
  ativo boolean not null default true,
  data_inicio date,
  data_fim date,
  criado_em timestamptz not null default now()
);

alter table lancamentos
  add column if not exists recorrencia_id uuid references recorrencias(id);

create index if not exists idx_lancamentos_recorrencia_data
  on lancamentos (recorrencia_id, data);
