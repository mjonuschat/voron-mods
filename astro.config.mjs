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
      head: [
        {
          tag: 'link',
          attrs: { rel: 'mask-icon', href: 'https://mjonuschat.github.io/voron-mods/mask-icon.svg', color: 'white' },
        },
        {
          tag: 'meta',
          attrs: { property: 'og:image', content: 'https://mjonuschat.github.io/voron-mods/cover.png' },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:image', content: 'https://mjonuschat.github.io/voron-mods/cover.png' },
        },
      ],
    }),
  ],
});
