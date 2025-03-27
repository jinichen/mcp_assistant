import { redirect } from 'next/navigation';
import { defaultLocale } from '../i18n';

export default function Home() {
  redirect(`/${defaultLocale}`);
}

export const runtime = 'edge';