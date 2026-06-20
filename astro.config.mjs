import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'Voron Guides',
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/mjonuschat/voron-mods' },
      ],
      sidebar: [
        { label: 'Guides', items: [{ autogenerate: { directory: 'docs/guides' } }] },
      ],
      customCss: ['./src/styles/custom.css'],
    }),
  ],
});
