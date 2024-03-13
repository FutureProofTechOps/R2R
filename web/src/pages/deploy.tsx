import { Info } from 'lucide-react';
import { useRouter } from 'next/router';
import { useState } from 'react';

import { CopyIcon } from '@/components/icons/CopyIcon';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/Button';
import {
  CardTitle,
  CardDescription,
  CardHeader,
  CardContent,
  CardFooter,
  Card,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import styles from '@/styles/Index.module.scss';
import { createClient } from '@/utils/supabase/component';

function Component() {
  const [secretPairs, setSecretPairs] = useState([{ key: '', value: '' }]);
  const [selectedApiKey, setSelectedApiKey] = useState('');
  const [availableApiKeys, setAvailableApiKeys] = useState([
    { value: 'key1', label: 'API Key 1' },
    { value: 'key2', label: 'API Key 2' },
    // Add more available API keys as needed
  ]);
  const [newPublicKey, setNewPublicKey] = useState('');
  const [newPrivateKey, setNewPrivateKey] = useState('');
  const [newApiKeyName, setNewApiKeyName] = useState('');
  const [pipelineName, setPipelineName] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const handleAddMore = () => {
    setSecretPairs([...secretPairs, { key: '', value: '' }]);
  };
  const router = useRouter();
  const supabase = createClient();

  const handleRemove = (index) => {
    const updatedPairs = [...secretPairs];
    updatedPairs.splice(index, 1);
    setSecretPairs(updatedPairs);
  };

  const handleSecretKeyChange = (index, value) => {
    const updatedPairs = [...secretPairs];
    updatedPairs[index].key = value;
    setSecretPairs(updatedPairs);
  };

  const handleSecretValueChange = (index, value) => {
    const updatedPairs = [...secretPairs];
    updatedPairs[index].value = value;
    setSecretPairs(updatedPairs);
  };

  const handleGenerateApiKey = () => {
    console.log('generating new api key...');
    // Generate a new public key and private key
    const newPublicKey = generatePublicKey();
    const newPrivateKey = generatePrivateKey();

    // Generate a default name for the API key
    const defaultName = `API Key ${availableApiKeys.length + 1}`;

    // Add the new API key to the available keys
    const newApiKey = { value: newPublicKey, label: defaultName };
    // setAvailableApiKeys([...availableApiKeys, newApiKey]);

    // Set the new public key, private key, and API key name in the state
    setNewPublicKey(newPublicKey);
    setNewPrivateKey(newPrivateKey);
    setNewApiKeyName(defaultName);

    // Select the newly generated API key
    setSelectedApiKey('generate');
  };

  const generatePublicKey = () => {
    // Generate a new public key (replace with your own logic)
    return `pk-${Math.random().toString(36)}`;
  };

  const generatePrivateKey = () => {
    // Generate a new private key (replace with your own logic)
    return `sk-${Math.random().toString(36)}`;
  };
  const handleApiKeyChange = (value) => {
    if (value === 'generate') {
      handleGenerateApiKey();
    } else if (value === 'No API Key') {
      setNewPublicKey('');
      setNewPrivateKey('');
      setSelectedApiKey(value);
    } else {
      setSelectedApiKey(value);
    }
  };

  const handleSubmit = async () => {
    // Prepare the form data

    const formData = {
      pipeline_name: pipelineName,
      repo_url: githubUrl,
      secret_pairs: secretPairs,
    };

    try {
      // Get the current session token
      const session = await supabase.auth.getSession();
      const token = session.data?.session?.access_token;

      if (!token) {
        // Handle case when token is not available
        console.error('Access token not found');
        // Display an error message to the user or redirect to login page
        return;
      }

      if (pipelineName === '') {
        alert('Please enter a pipeline name');
        return;
      }

      if (githubUrl === '') {
        alert('Please enter a GitHub URL');
        return;
      }

      // check if any private keys or values are empty
      for (let i = 0; i < secretPairs.length; i++) {
        if (secretPairs[i].key === '' || secretPairs[i].value === '') {
          alert('Please enter a secret key and value');
          return;
        }
      }
      setIsLoading(true);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_CLOUD_REMOTE_SERVER_URL}/deploy`,
        {
          method: 'POST',
          headers: new Headers({
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(formData),
        }
      );

      if (response.ok) {
        // Pipeline creation successful
        console.log('Pipeline created successfully');
        // Reset the form fields
        // Redirect to a success page or display a success message
        // Wait for a random duration between 1 to 2 seconds before navigating to the home page
        const delay = Math.floor(Math.random() * 1000) + 1000; // Random duration between 1000 to 2000 milliseconds
        setTimeout(() => {
          setPipelineName('');
          setGithubUrl('');
          setSelectedApiKey('');
          setSecretPairs([{ key: '', value: '' }]);
          setNewPublicKey('');
          setNewPrivateKey('');
          setIsLoading(false);
          router.push('/');
        }, delay);
      } else {
        // Pipeline creation failed
        console.error('Pipeline creation failed');
        // Display an error message to the user
        alert('Failed to create the pipeline. Please try again.');
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error creating pipeline:', error);
      // Display an error message to the user
      alert('An error occurred while creating the pipeline. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full mt-2 cursor-pointe bg-zinc-800 ">
      <CardHeader>
        <CardTitle>Deploy a RAG pipeline</CardTitle>
        <CardDescription>
          To deploy a new Pipeline, import an existing GitHub Repository or
          select a template.
        </CardDescription>
      </CardHeader>
      <CardFooter>
        <CardContent className="space-y-4 w-full">
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-8 left-content">
              <div className="mb-8">
                <div className="space-y-2 mb-4">
                  <Label htmlFor="project-name">Pipeline Name</Label>
                  <Input
                    placeholder="Name Your Pipeline"
                    className="w-full"
                    onChange={(e) => setPipelineName(e.target.value)}
                    value={pipelineName}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="github-url">GitHub URL</Label>
                  <Input
                    key="github-url"
                    id="github-url"
                    placeholder="Enter your GitHub URL"
                    className="w-full"
                    onChange={(e) => setGithubUrl(e.target.value)}
                    value={githubUrl}
                  />
                </div>
              </div>

              {secretPairs.map((pair, index) => (
                <div
                  key={index}
                  className="grid grid-cols-12 gap-4 items-center mb-2"
                >
                  <div className="col-span-5 space-y-2">
                    {index === 0 && (
                      <Label htmlFor={`secret-key-${index + 1}`}>
                        Secret Key(s)
                        <TooltipProvider>
                          <Tooltip delayDuration={0}>
                            <TooltipTrigger>
                              <Info className="h-4 w-4 pt-1 text-gray-500" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>
                                Secrets are encrypted at all times during
                                transmission and storage.
                                <br />
                                <br />
                                SciPhi&apos;s infrastructure is hosted on Google
                                Cloud.
                                <br />
                                All secrets are provisioned through Google
                                Cloud&apos;s Secret Manager.
                                <br />
                                <a
                                  href="https://docs.sciphi.ai/getting-started/deploying-a-pipeline#providing-secrets"
                                  className="text-blue-400 font-bold"
                                >
                                  Read more here.
                                </a>{' '}
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </Label>
                    )}
                    <Input
                      id={`secret-key-${index + 1}`}
                      placeholder="e.g. `OPENAI_API_KEY`"
                      value={pair.key}
                      onChange={(e) =>
                        handleSecretKeyChange(index, e.target.value)
                      }
                    />
                  </div>
                  <div className="col-span-6 space-y-2">
                    {index === 0 && (
                      <Label htmlFor={`secret-value-${index + 1}`}>
                        Secret Value(s)
                      </Label>
                    )}
                    <Input
                      id={`secret-value-${index + 1}`}
                      placeholder="e.g. `sk-bDaW...`"
                      value={pair.value}
                      type="password"
                      onChange={(e) =>
                        handleSecretValueChange(index, e.target.value)
                      }
                    />
                  </div>
                  <div className="col-span-1 flex justify-end">
                    <button
                      className={
                        'bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-xs ' +
                        (index === 0 ? 'mt-7' : '')
                      }
                      onClick={() => handleRemove(index)}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
              <div className="flex justify-start mt-2 mb-3">
                <Button
                  variant="primary"
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded text-xs"
                  onClick={handleAddMore}
                >
                  {secretPairs.length === 0 ? 'Add secret' : 'Add more secrets'}
                </Button>
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-key">Select API Key</Label>
                <TooltipProvider>
                  <Tooltip delayDuration={0}>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 pt-1 text-gray-500" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>
                        Selecting an API key will protect your application
                        during deployment.
                        <br />
                        API keys enable secure communication between your
                        application and the server.
                        <br />
                        <br />
                        Select `No API Key` to allow unauthenticated access to
                        your application.
                        <br />
                        <br />
                        ** Currently disabled **
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Select
                  value={selectedApiKey}
                  onValueChange={handleApiKeyChange}
                  disabled={true}
                >
                  <SelectTrigger>
                    {/* className="w-[300px]"> */}
                    <SelectValue placeholder="Select an API Key" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>Available API Keys</SelectLabel>
                      {availableApiKeys.map((apiKey) => (
                        <SelectItem key={apiKey.value} value={apiKey.value}>
                          {apiKey.label}
                        </SelectItem>
                      ))}
                      <SelectItem key="No API Key" value={'No API Key'}>
                        No API Key
                      </SelectItem>
                      <SelectItem value="generate">
                        Generate New API Key
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
                {newPublicKey && (
                  <div className="mt-2">
                    <Label htmlFor="api-key-name">
                      API Key Name (optional)
                    </Label>
                    <Input
                      id="api-key-name"
                      placeholder={newApiKeyName}
                      value={newApiKeyName}
                      onChange={(e) => setNewApiKeyName(e.target.value)}
                    />
                  </div>
                )}
                {newPublicKey && (
                  <div className="mt-2">
                    <Label>New Public Key:</Label>
                    <Input value={newPublicKey} readOnly />
                  </div>
                )}
                {newPrivateKey && (
                  <div className="mt-2">
                    <Label>New Private Key:</Label>
                    <Input value={newPrivateKey} readOnly />
                    <p className="text-red-500 mt-1">
                      Warning: Your private key will not be saved. Please store
                      it securely.
                    </p>
                  </div>
                )}
              </div>
              <div className="flex justify-end mt-4">
                <Button
                  variant={
                    pipelineName &&
                    githubUrl &&
                    secretPairs.every((pair) => pair.key && pair.value) &&
                    !isLoading // Ensure the button is not in the loading state
                      ? 'filled'
                      : 'disabled'
                  }
                  className={`w-1/3 h-8 py-1 ${
                    !pipelineName ||
                    !githubUrl ||
                    secretPairs.some((pair) => !pair.key || !pair.value) ||
                    isLoading
                      ? 'bg-gray-400 hover:bg-gray-400 cursor-not-allowed text-white' // Darken the button when loading
                      : 'bg-blue-500 hover:bg-blue-700 text-white'
                  }`}
                  onClick={handleSubmit}
                  disabled={isLoading}
                >
                  {isLoading ? 'Deploying...' : 'Deploy'}
                </Button>
              </div>
            </div>
            <div className="col-span-4 right-content">
              <div className="text-lg font-bold text-indigo-500 mb-4">
                <a
                  href="/docs/getting-started/rag-templates"
                  className="hover:underline"
                >
                  R2R Templates
                </a>
              </div>
              <Card
                className="w-full mt-2 cursor-pointer hover:bg-blue-100 transition-colors duration-300 bg-blue-200 border-l-4 border-blue-400 relative"
                onClick={() => {
                  console.log('Card clicked!');
                  setPipelineName('Basic RAG');
                  setGithubUrl(
                    'https://github.com/SciPhi-AI/R2R-basic-rag-template'
                  );
                }}
              >
                {/* <div className="absolute top-2 right-2">
                  <CopyIcon className="h-8 w-8" />
                </div> */}
                <CardHeader className="flex items-start justify-start">
                  <CardTitle className="text-blue-800">Basic RAG</CardTitle>
                  <CardDescription className="text-zinc-800">
                    Ingest documents and answer questions
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card
                className="w-full mt-2 cursor-pointer hover:bg-green-100 transition-colors duration-300 bg-green-200 border-l-4 border-green-400 relative"
                onClick={() => {
                  console.log('Card clicked!');
                  setPipelineName('Synthetic Queries');
                  setGithubUrl(
                    'https://github.com/SciPhi-AI/R2R-synthetic-queries-template'
                  );
                }}
              >
                {/* <div className="absolute top-2 right-2">
                  <CopyIcon className="h-8 w-8" />
                </div> */}
                <CardHeader className="flex items-start justify-start">
                  <CardTitle className="text-green-800">
                    Synthetic Query RAG
                  </CardTitle>
                  <CardDescription className="text-zinc-800">
                    RAG w/ LLM generated synthetic queries
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card
                className="w-full mt-2 cursor-pointer hover:bg-red-100 transition-colors duration-300 bg-red-200 border-l-4 border-red-400 relative"
                onClick={() => {
                  console.log('Card clicked!');
                  setPipelineName('Web RAG');
                  setGithubUrl(
                    'https://github.com/SciPhi-AI/R2R-web-rag-template'
                  );
                }}
              >
                <CardHeader className="flex items-start justify-start">
                  <CardTitle className="text-red-800">Web RAG</CardTitle>
                  <CardDescription className="text-zinc-800">
                    RAG performed over web search results
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </CardContent>
      </CardFooter>
    </Card>
  );
}

export default function Deploy() {
  return (
    <Layout>
      <main className={styles.main}>
        <div>
          <Component />
        </div>
      </main>
    </Layout>
  );
}
