import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * Creates a sidebar
 *
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation
 *
 The sidebars can be generated from the filesystem, or explicitly defined here.
 */
const sidebars: SidebarsConfig = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  tutorialSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'overview',
        'installation',
        'changelog',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/cli',
        'guides/server',
        'guides/ui',
        'guides/configuration',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/json-schema',
      ],
    },
    {
      type: 'category',
      label: 'Advanced',
      items: [
        'advanced/ci-workflow',
        'advanced/failures',
      ],
    },
    'examples',
    'integrations',
  ],
};

export default sidebars;
