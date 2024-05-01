import {exposed} from 'newsroom-core';
import {STTCoverageVersionPreviewField} from './stt/STTCoverageVersionPreviewField';

exposed.agenda.registerCoveragePreviewFieldComponent('sttversion', STTCoverageVersionPreviewField);
