import Image from 'next/image';
import { useRouter } from 'next/router';

import styles from './styles.module.scss';

function WorkspacesSelect() {
  const router = useRouter();
  const pipelineId = router.asPath.split('/').pop();

  console.log('Navbar pipelineId = ', pipelineId);

  return (
    <div className={styles.container}>
      <Image
        alt={`sciphi.png`}
        src={`/images/sciphi.png`}
        width={48}
        height={48}
        className={styles.logo}
      />
      <div className={styles.divider}></div>

      <div className={styles.userPanel}>
        <div className={styles.currentWorkspace}>
          <div>
            <Image
              src="/images/dummy_logo.png"
              alt="Acme Co."
              width="30"
              height="30"
              className={styles.workspaceIcon}
            />
          </div>
          Acme Co.
        </div>
      </div>
      {router.pathname !== '/' && pipelineId && (
        <>
          <div className={styles.divider}></div>
          <div className={styles.userPanel}>
            Pipeline: <code>{pipelineId.slice(0, 8)}...</code>
          </div>
        </>
      )}
    </div>
  );
}

export { WorkspacesSelect };
