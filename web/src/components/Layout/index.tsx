// components/Layout.tsx
import Head from 'next/head';
import React, { ReactNode } from 'react';

import styles from '@/styles/Index.module.scss';

import { MainMenu } from '../MainMenu';
import { SubNavigationMenu } from '../SubNavigationMenu';

type Props = {
  children: ReactNode;
};

const Layout: React.FC<Props> = ({ children }) => (
  <div className={styles.container}>
    <Head>
      <title>SciPhi</title>
      <link rel="icon" href="/favicon.ico" />
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link
        href="https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;600;700&display=swap"
        rel="stylesheet"
      />
    </Head>

    <header className={styles.topBar}>
      <MainMenu />
    </header>
    <SubNavigationMenu />
    {children}
  </div>
);

export default Layout;
