// src/pages/ReportIssuePage.tsx
import React, { useState } from 'react';
import { issueReportingService } from '../services/IssueReportingService';
import { useQFix } from '../contexts/QFixProvider';
import { PrimaryButton, Stack, TextField } from '@fluentui/react';


const ReportIssuePage: React.FC = () => {
  const { incrementIssueCount} = useQFix();
  const [description, setDescription] = useState('');
  const [photoPosition, setPhotoPosition] = useState<string|null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  const fileInput = React.createRef<HTMLInputElement>();  


  const handleSave = async () => {
    if (photo && description) {
      const submitPosition=localStorage.getItem('position');
      await issueReportingService.submitIssue(description, photo, photoPosition||'' , submitPosition||'');
      setDescription('');
      setPhoto(null);
      setPhotoPosition(null);
      fileInput.current!.value = '';
      incrementIssueCount();
    }
  };

  return (
    <Stack horizontalAlign="center" verticalAlign="center" styles={{ root: { height: 'calc( 100vh - 64px)',overflow:'hidden' } }}>
      <div>
      <input ref={fileInput} type="file" accept="image/*;capture=camera"  onChange={(e) => 
        {
        setPhoto(e.target.files?.[0] || null);
        setPhotoPosition(localStorage.getItem('position'));
        }} />
      </div>
      <div>
      <TextField 
      style={{height:'30vh',maxHeight: '300px'}}
      placeholder="Description" value={description} resizable={false}  multiline onChange={(e,value) => setDescription(value||'')} />
      </div>
      <div>
      <PrimaryButton disabled={!(photo && description && photoPosition)} onClick={handleSave} text='Submit' />
      </div>
      </Stack>
  );
};

export default ReportIssuePage;