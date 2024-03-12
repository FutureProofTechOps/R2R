import { forwardRef, useState, useEffect } from 'react';
import Link from 'next/link';
import clsx from 'clsx';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useRouter } from 'next/router';

import { Code } from '@/components/ui/Code'; // Ensure this import is correct

function TopLevelNavItem({
  href,
  children,
  isActive,
}: {
  href: string;
  children: React.ReactNode;
  isActive: boolean;
}) {
  return (
    <li>
      <Link href={href} legacyBehavior>
        <a
          className={clsx(
            'text-sm leading-5 transition',
            isActive
              ? 'text-indigo-500'
              : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white'
          )}
        >
          <Code>{children}</Code>
        </a>
      </Link>
    </li>
  );
}

export const SubNavigationBar = forwardRef<
  React.ElementRef<'div'>,
  {
    className?: string;
    isPipelineRoute: boolean;
    pipelineId: string | null;
    pathSegments: string[];
  }
>(({ className, isPipelineRoute, pipelineId, pathSegments = [] }, ref) => {
  const router = useRouter();
  const { scrollY } = useScroll();
  const bgOpacityLight = useTransform(scrollY, [0, 72], [0.5, 0.9]);
  const bgOpacityDark = useTransform(scrollY, [0, 72], [0.2, 0.8]);
  // State to manage active path
  const [activePath, setActivePath] = useState(router.asPath);

  // Effect to update active path on route change
  useEffect(() => {
    const handleRouteChange = (url: string) => {
      setActivePath(url);
    };

    router.events.on('routeChangeComplete', handleRouteChange);

    // Cleanup listener on component unmount
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router.events]);

  const navItems =
    isPipelineRoute && pipelineId
      ? [
          {
            path: `/`,
            label: <span className="text-3xl">←</span>, // Use a larger text size and bolder font
          },
          {
            path: `/pipeline/${pipelineId}`,
            label: 'Pipeline',
          },
          {
            path: `/pipeline/${pipelineId}/retrievals`,
            label: 'Retrievals',
          },
          {
            path: `/pipeline/${pipelineId}/embeddings`,
            label: 'Embeddings',
          },
        ]
      : [
          {
            path: '/',
            label: 'Home',
          },
        ];

  return (
    <motion.div
      ref={ref}
      className={clsx(
        className,
        'fixed inset-x-0 top-10 z-40 flex h-10 items-center justify-between gap-12 px-4 transition sm:px-6 lg:z-30 lg:px-8 backdrop-blur-sm dark:backdrop-blur bg-zinc-800'
      )}
      style={
        {
          '--bg-opacity-light': bgOpacityLight,
          '--bg-opacity-dark': bgOpacityDark,
        } as React.CSSProperties
      }
    >
      <div className="flex items-center justify-between w-full">
        <nav className="flex">
          <ul role="list" className="flex items-center gap-3 pl-3">
            {navItems.map((item) => (
              <TopLevelNavItem
                key={item.path}
                href={item.path}
                isActive={(pathSegments || []).includes(
                  item.path.split('/').pop() ?? ''
                )}
              >
                {item.label}
              </TopLevelNavItem>
            ))}
          </ul>
        </nav>
      </div>
    </motion.div>
  );
});
